# Copyright 2004 Darius Bacon, under the terms of the MIT X license.

from BaseHTTPServer import BaseHTTPRequestHandler
import cgi
import re
import sys
import urllib
import urlparse

import html


def parse_qs(string):
    query = cgi.parse_qs(string)
    result = {}
    for key in query:
	if len(query[key]) != 1:
	    raise 'Multiple values for key', key
	result[key] = query[key][0]
    return result

def make_query(uri, **kwargs):
    return '%s?%s' % (uri, urllib.urlencode(kwargs))


def make_dispatching_handler_class(dispatcher):

    class DispatchingHTTPRequestHandler(BaseHTTPRequestHandler):

	def do_GET(self):
	    self.verb = 'GET'
	    self._parse(parse_qs)
	    dispatcher.handle(self)

	def do_POST(self):
	    self.verb = 'POST'
	    self._parse(self._parse_post_params)
	    dispatcher.handle(self)

	def _parse_post_params(self, url_query_str):
            # XXX reply 400 Bad Request if there's no Content-Length header
	    content_length = int(self.headers.getheader('Content-Length'))
	    if content_length == 0:
		data = ''
	    else:
		data = self.rfile.read(content_length)
	    return parse_qs(data)

	def _parse(self, parse_query):
	    # XXX path and path_str need better-distinguishing names
	    _, _, self.path_str, _, self.query_str, _ = \
	      urlparse.urlparse(self.path)
	    if self.path_str[0:1] == '/': # XXX does this ever not happen?
		self.path_str = self.path_str[1:]
	    self.remaining_path = self.path_str
	    try:
                self.query = None
		self.query = parse_query(self.query_str)
	    except:
		self._complain(sys.exc_info()[:2], self.query)
		print 'query_str = [', self.query_str, ']'
		raise

	def _complain(self, exception_type_and_value, query):
	    complaint = cgi.escape('%s: %s' % exception_type_and_value)
	    self.reply(['Error: ' + complaint,
			html.P(),
			repr(query)])

	def redirect(self, uri):
	    self.send_response(302, uri)
	    self.send_header('Location', uri)
	    self.send_header('Content-type', 'text/html')
	    self.end_headers() 
	    # XXX should use html module for safety
            explanation = 'Redirect to <a href="%s">%s</a>' % (uri, uri)
	    self.wfile.write(explanation.encode('utf8'))

	def reply(self, body_html):
	    self.send_response(200)
	    self.send_header('Content-type', 'text/html')
	    self.end_headers()
	    self.wfile.write(html.emit(body_html).encode('utf8'))

	def reply_404(self):
	    self.send_error(404, 'Object not found: %s' % self.path)

    return DispatchingHTTPRequestHandler


class MetaDispatcher:

    def __init__(self):
	self.getters = self._collect('get_')
	self.posters = self._collect('post_')

    def _collect(self, prefix):
	pairs = [(_parse_name(name[len(prefix):]), getattr(self, name))
		 for name in dir(self) if name.startswith(prefix)]
	return tuple(pairs)

    def shut_down(self):
        """Called when the webserver is shutting down. Save your state,
        or whatever."""
        pass

    def handle(self, request):
	if request.verb == 'GET':  return self._handle(self.getters, request)
	if request.verb == 'POST': return self._handle(self.posters, request)
	request.send_error(400, 'Unsupported verb')  # XXX look up right code

    def _handle(self, handlers, request):
	handler, params = _lookup(handlers, request.remaining_path)
	if handler is None:
	    subdir, remaining = self._subdir_lookup(request.remaining_path)
	    if subdir is not None:
		# XXX breaks encapsulation
		# XXX need to use tail of path in subdir
		request.remaining_path = remaining
		return subdir.handle(request)
	    return request.reply_404()
	try:
            self.invoke(handler, request, params)
	except:
	    request._complain(sys.exc_info()[:2], request.query)
	    raise

    def invoke(self, handler, request, params):
        handler(request, *params, **request.query)

    def _subdir_lookup(self, path_str):
	if hasattr(self, 'subdirs'):
	    first, rest = _split(path_str)
	    if first in self.subdirs:
		return self.subdirs[first], rest
	return None, None

def _split(path):
    i = path.find('/')
    if 0 < i: return path[:i], path[i+1:]
    else:     return path, ''

def _lookup(pairs, path_str):
    for (name, pattern), handler in pairs:
	m = pattern.match(path_str)
	if m:
	    return handler, m.groups()
    return None, None

def _parse_name(name):
    parts = name.split('_')
    patterns = [([part, r'([^/]+)'][part == 'V']) for part in parts]
    name = '/'.join(patterns) + '$'
    return name, re.compile(name)

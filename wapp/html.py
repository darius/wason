# Copyright 2004, 2007 Darius Bacon, under the terms of the MIT X license.

import cgi


def emit(obj, attribute=False):
    if type(obj) == list:
	return ''.join([emit(element) for element in obj])
    if type(obj) == str or type(obj) == unicode:
	return cgi.escape(obj, attribute)
    if type(obj) == type(emit):
	return obj()		# XXX what if attribute=True?
    raise 'Bad type', obj

def emit_attributes(dict):
    attrs = []
    for key in dict:
	attrs.append(' %s="%s"' % (cgi.escape(key), 
				   emit(dict[key], attribute=True)))
    return ''.join(attrs)

def make_tag_emitter(tag):
    def make(_='', **kwargs):
	def emitter():
	    return '<%s%s>%s</%s>' % (tag,
				      emit_attributes(kwargs), emit(_),
				      tag)
	return emitter
    return make

def make_lonetag_emitter(tag):
    def make(**kwargs):
	def emitter():
	    return '<%s%s>' % (tag, emit_attributes(kwargs))
	return emitter
    return make

def make_entity(name):
    def entity():
        return '&%s;' % name
    return entity

A        = make_tag_emitter('a')
B        = make_tag_emitter('b')
Code     = make_tag_emitter('code')
Form     = make_tag_emitter('form')
H1       = make_tag_emitter('h1')
H2       = make_tag_emitter('h2')
H3       = make_tag_emitter('h3')
Hr       = make_tag_emitter('hr')
I        = make_tag_emitter('i')
Img      = make_tag_emitter('img')
Li       = make_tag_emitter('li')
Pre      = make_tag_emitter('pre')
Table    = make_tag_emitter('table')
TextArea = make_tag_emitter('textarea')
Tbody    = make_tag_emitter('tbody')
Td       = make_tag_emitter('td')
Th       = make_tag_emitter('th')
Thead    = make_tag_emitter('thead')
Tr       = make_tag_emitter('tr')
# XXX Tr and Td should leave out the closing tag
Ul       = make_tag_emitter('ul')

Br       = make_lonetag_emitter('br')
Input    = make_lonetag_emitter('input')
P        = make_lonetag_emitter('p')
Hr       = make_lonetag_emitter('hr')

lsquo     = make_entity('#8216')
rsquo     = make_entity('#8217')
ldquo     = make_entity('#8220')
rdquo     = make_entity('#8221')


# Some conveniences:

def link(url, body):
    return A(href=url, _=body)

def submit(value, name=None):
    if name is None:
	return Input(type='submit', value=str(value))
    else:
	return Input(type='submit', name=name, value=str(value))

def singlequote(h): return [lsquo, h, rsquo]
def doublequote(h): return [ldquo, h, rdquo]

def rsquotify(string):
    result = []
    for part in string.split("'"):
        result.append(part)
        result.append(rsquo)
    return result[:-1]

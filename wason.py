import datetime

import wapp
from wapp import html


class Triplet:
    def __init__(self, n1, n2, n3):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
    def is_awesome(self):
        return self.n1 < self.n2 < self.n3
    def __str__(self):
        return '%s, %s, %s' % (self.n1, self.n2, self.n3)
    def rate(self):
        if self.is_awesome():
            return "%s is an AWESOME triplet!" % self
        else:
            return "%s is not remotely awesome. Sorry." % self
    def display(self, considered_awesome):
        judgment = awesomeness(considered_awesome)
        actually = awesomeness(self.is_awesome())
        if judgment == actually:
            def ornament(h): return h
        else:
            def ornament(h): return html.B(h)
        return html.Tr([html.Td(ornament(str(self))),
                        html.Td(ornament(judgment)),
                        html.Td(ornament(actually))])
    def as_row(self):
        return html.Tr([html.Td(str(self)),
                        html.Td(awesomeness(self.is_awesome()))])
    def satisfies(self, rule):
        return rule.judge(self.n1, self.n2, self.n3)
                
def awesomeness(is_awesome):
    if is_awesome:
        return "awesome"
    return "not awesome"


test_triplets = [
    Triplet(3,6,9),
    Triplet(6,4,2),
    Triplet(8,10,12),
    Triplet(1,17,33),
    Triplet(18,9,0),
    Triplet(1,7,3),
    Triplet(3,5,7),
    Triplet(2,9,15),
    Triplet(5,10,15),
    Triplet(3,1,4),
    Triplet(5,5,5),
    ]


class RightRule:
    in_english = "awesome triplets are simply triplets in which each number is greater than the previous one."
    def judge(self, n1, n2, n3):
        return Triplet(n1, n2, n3).is_awesome()
    def explain(self, nerrors):
        # XXX add some info about positive bias
        if nerrors:
            return ["It looks like you've discovered the correct rule: ",
                    self.in_english,
                    " (Though you made %d error%s.)" % (nerrors, pluralize(nerrors))]
        return ["Congratulations! You performed perfectly on this test, discovering the correct rule: ",
                self.in_english,
                html.P(),
                "It may surprise you to know this, but in tests carried out by Peter Wason, only 20% of subjects performed as well as you have."]

def pluralize(n):
    if n != 1:
        return "s"
    return ""

class Add2Rule:
    def judge(self, n1, n2, n3):
        return n2 == n1 + 2 and n3 == n1 + 4
    def explain(self, nerrors):
        return enlighten("It looks like you thought the rule was that awesome triplets contain numbers which increase by 2.")

class MultiplesRule:
    def judge(self, n1, n2, n3):
        return n2 == 2*n1 and n3 == 3*n1
    def explain(self, nerrors):
        return enlighten("It looks as though you thought the rule was that awesome triplets contained three successive multiples of the same number, like 3,6,9, or 6,12,18.")

class SameIntervalRule:
    def judge(self, n1, n2, n3):
        return n3 + n1 == 2*n2
    def explain(self, nerrors):
        return enlighten("It looks as though you thought the rule was that awesome triplets contain numbers separated by the same interval.")

candidate_rules = [RightRule(), Add2Rule(), MultiplesRule(), SameIntervalRule()]

def enlighten(preamble):
    h = [preamble, " In fact, ", RightRule().in_english,
         html.P(),
         # XXX rephrase the 'you invented' when no rule matches
         "The rule for awesomeness was a fairly simple one, but you invented a more complicated, more specific rule, which happened to fit the first triplet you saw. In experimental tests, it has been found that 80% of subjects do just this, and then never test any of the pairs that ",
         html.I(html.rsquotify("don't")),
         " fit their rule. If they did, they would immediately see the more general rule that was applying. This is a case of what psychologists call ",
         html.singlequote("positive bias"),
         ". It is one of the many biases, or fundamental errors, which beset the human mind.",
         html.P(),
         "There is a thriving community of rationalists at the website ",
         html.link('http://www.lesswrong.com', "Less Wrong"),
         html.rsquotify(" who are working to find ways to correct these fundamental errors. If you'd like to learn how to perform better with the hardware you have, you may want to pay them a visit.")]
    return h


def intro():
    h = [html.P(),
         html.rsquotify("Hi there! We're going to play a game based on a classic cognitive science experiment first performed by Peter Wason in 1960 (references at the end)."),
         html.P(),
         html.rsquotify("Here's how it works. I'm thinking of a rule which separates sequences of three numbers into "),
         html.singlequote("awesome"),
         html.rsquotify(" triplets, and not-so-awesome triplets. I'll tell you for free that 2 4 6 is an awesome triplet."),
         html.P(),
         html.rsquotify("What you need to do is to figure out which rule I'm thinking of. To help you do that, I'm going to let you experiment for a bit. Enter any three numbers, and I'll tell you whether they are awesome or not. You can do this as many times as you like, so please take your time."),
         html.P(),
         html.rsquotify("When you're sure you know what the rule is, hit "),
         html.singlequote("Continue"),
         html.rsquotify(", and I'll test you to see if you've correctly worked out what the rule is."),
         html.P(),
         html.Form(method='POST', action='/start',
                   _=["Enter three numbers: ",
                      html.Input(name='triple'),
                      html.submit('Start')])]
    return h

footer = [html.P(), "You can ", html.link('/', "start over"), "."]


class Root(wapp.Resource):
    def __init__(self):
        wapp.Resource.__init__(self)
        self.games = []
        log('starting')
    def get_(self, request):
        request.reply(intro())
    def get_start(self, request):
        # For some reason we're getting "GET /start" requests;
        # let's treat them like "GET /".
        self.get_(request)
    def post_start(self, request, triple=''):
        log('start %d %r', len(self.games), triple)
        g = Game(len(self.games))
        self.games.append(g)
        return g.probe(request, triple)
    def post_games_V_probe(self, request, gid='', triple=''):
        log('probe %r %r', gid, triple)
        try:
            g = self.get_game(gid)
        except ValueError:
            request.reply_404()
            return
        return g.probe(request, triple)
    def post_games_V_quiz(self, request, gid='', yes='', no=''):
        log('quiz %r %r %r', gid, yes, no)
        try:
            g = self.get_game(gid)
        except ValueError:
            request.reply_404()
            return
        return g.quiz(request, yes, no)
    def get_game(self, gid):
        n = int(gid)
        if not (0 <= n < len(self.games)): raise ValueError()
        return self.games[n]


class Game:

    def __init__(self, id):
        self.id = id
        self.probes = []
        self.tests = []

    def probe(self, request, triple):
        rating = self.parse_probe(triple)
        h = [rating,
             html.P(),
             html.Form(method='POST', action='/games/%d/probe' % self.id,
                       _=["Enter three numbers: ",
                          html.Input(name='triple'),
                          html.submit('Enter')]),
             html.Form(method='POST', action='/games/%d/quiz' % self.id,
                       _=[html.rsquotify("Or if you're sure what the rule is: "),
                          html.submit('Continue')]),
             html.P(),
             self.probe_history(),
             footer]
        request.reply(h)

    def probe_history(self):
        if not self.probes:
            return []
        return ["For reference, your triplets so far:",
                html.P(),
                html.Table(rules='all',
                           _=[triplet.as_row() for triplet in self.probes])]

    def parse_probe(self, triple):
        try:
            n1, n2, n3 = map(as_number, triple.replace(',', ' ').split())
        except ValueError:
            return [str(triple),
                    html.rsquotify(" doesn't look like a triplet of numbers to me.")]
        t = Triplet(n1, n2, n3)
        self.probes.append(t)
        return t.rate()

    def quiz(self, request, yes, no):
        if (yes or no) and len(self.tests) < len(test_triplets):
            self.tests.append(yes != '')
        if len(self.tests) == len(test_triplets):
            return self.evaluate(request)
        triplet = test_triplets[len(self.tests)]
        h = [html.rsquotify("So, you're pretty sure what the rule is now? Cool. I'm going to give you some sets of numbers, and you can tell me whether they seem awesome to you or not."),
             html.P(),
             self.quiz_history(),
             html.Form(method='POST', action='/games/%d/quiz' % self.id,
                       _=["Would you say that %s looks like an awesome triplet? " % triplet,
                          html.submit('Yes', 'yes'),
                          html.submit('No', 'no')]),
             footer]
        request.reply(h)

    def quiz_history(self):
        return [["You judged %s %s." % (triplet, awesomeness(considered_awesome)),
                 html.Br()]
                for triplet, considered_awesome in zip(test_triplets, self.tests)]

    def evaluate(self, request):
        h1 = html.Table(rules='all',
                        _=[[html.Tr([html.Th("Triplet"),
                                     html.Th("Your judgment"),
                                     html.Th("In fact, it's")])]
                           +[triplet.display(considered_awesome)
                             for triplet, considered_awesome in zip(test_triplets, self.tests)]])
        errors = self.match_rules()
        bestscore, besttest = min((nerrors_k, k) for k, nerrors_k in enumerate(errors))
        log('evaluate %r %r %r', self.id, besttest, bestscore)
        if bestscore >= 3:
            h2 = enlighten(html.rsquotify("I'm not sure what rule you settled on."))
        else:
            h2 = candidate_rules[besttest].explain(bestscore)
        h3 = [html.rsquotify("If you'd like to learn more about positive bias, you may enjoy the article "),
              html.link('http://www.overcomingbias.com/2007/08/positive-bias-l.html',
                        html.singlequote("Positive Bias: Look Into the Dark")),
              ".",
              html.P(),
              html.rsquotify("If you'd like to learn more about the experiment which inspired this test, look for a paper titled "),
              html.singlequote("On the failure to eliminate hypotheses in a conceptual task"), 
              " (Quarterly Journal of Experimental Psychology, 12: 129-140, 1960)."]
        request.reply([h1, html.P(), h2, html.P(), h3, footer])

    def match_rules(self):
        "Return the error count for each rule in candidate_rules."
        return [sum([considered_awesome != triplet.satisfies(rule)
                     for triplet, considered_awesome in zip(test_triplets, self.tests)])
                for rule in candidate_rules]

def as_number(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


logfile = open('log', 'a', 1) # 1 for line-buffering

def log(format, *args):
    timestamp = datetime.datetime.utcnow().isoformat()
    logfile.write('%s %s\n' % (timestamp, format % args))


if __name__ == '__main__':
    wapp.main(Root())

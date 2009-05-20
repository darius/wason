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
        return '%d, %d, %d' % (self.n1, self.n2, self.n3)
    def rate(self):
        if self.is_awesome():
            return "%s is an AWESOME triplet!" % self
        else:
            return "%s is not remotely awesome. Sorry." % self
    def display(self, considered_awesome):
        return """\
You thought that %s was %s.
In fact it is %s.""" % (self, 
                        awesomeness(considered_awesome),
                        awesomeness(self.is_awesome()))
    def as_row(self):
        return html.Tr(_=[html.Td(_=str(self)),
                          html.Td(_=awesomeness(self.is_awesome()))])
    def quiz(self, considered_awesome):
        n1, n2, n3 = self.n1, self.n2, self.n3
        tests = [self.is_awesome(),
                 n2 == n1 + 2 and n3 == n1 + 4,
                 n2 == 2*n1 and n3 == 3*n1,
                 n3 + n1 == 2*n2]
        return [considered_awesome != test for test in tests]
                

def awesomeness(is_awesome):
    if is_awesome:
        return "awesome"
    return "not awesome"

    
def intro():
    s = [
        html.P(),
        "Hi there! We're going to play a game based on a classic cognitive science experiment first performed by Peter Wason in 1960 (references at the end).",
        html.P(),
        "Here's how it works. I'm thinking of a rule which separates sequences of three numbers into 'awesome' triplets, and not-so-awesome triplets. I'll tell you for free that 2 4 6 is an awesome triplet.",
        html.P(),
        "What you need to do is to figure out which rule I'm thinking of. To help you do that, I'm going to let you experiment for a bit. Enter any three numbers, and I'll tell you whether they are awesome or not. You can do this as many times as you like, so please take your time.",
        html.P(),
        "When you're sure you know what the rule is, hit 'Continue', and I'll test you to see if you've correctly worked out what the rule is.",
        html.P(),
        html.Form(method='POST', action='/start',
                  _=["Enter three numbers separated by spaces: ",
                     html.Input(name='triple'),
                     html.submit('Start')])
        ]
    return s


logfile = open('log', 'a')

class Root(wapp.Resource):
    def __init__(self):
        wapp.Resource.__init__(self)
        self.games = []
    def get_(self, request):
        request.reply(intro())
    def post_start(self, request, triple=''):
        logfile.write('start %r\n' % triple)
        logfile.flush()
        g = Game(len(self.games))
        self.games.append(g)
        return g.probe(request, triple)
    def post_games_V_probe(self, request, gid='', triple=''):
        logfile.write('probe %r %r\n' % (gid, triple))
        logfile.flush()
        try:
            g = self.get_game(gid)
        except ValueError:
            request.reply_404()
            return
        return g.probe(request, triple)
    def post_games_V_quiz(self, request, gid='', yes='', no=''):
        logfile.write('quiz %r %r %r\n' % (gid, yes, no))
        logfile.flush()
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
                       _=["Enter three numbers separated by spaces: ",
                          html.Input(name='triple'),
                          html.submit('Enter')]),
             html.Form(method='POST', action='/games/%d/quiz' % self.id,
                       _=["Or if you're sure what the rule is: ",
                          html.submit('Continue')]),
             html.P(),
             self.probe_history()]
        request.reply(h)
    def probe_history(self):
        return html.Table(_=[triplet.as_row() for triplet in self.probes])
    def parse_probe(self, triple):
        try:
            s1, s2, s3 = triple.split()
        except ValueError:
            return "%s is not a triple." % triple
        try:
            n1, n2, n3 = int(s1), int(s2), int(s3)
        except ValueError:
            return "%s is not a triple of numbers." % triple
        t = Triplet(n1, n2, n3)
        self.probes.append(t)
        return t.rate()
    def quiz(self, request, yes, no):
        if yes or no:
            self.tests.append(yes != '')
        if len(self.tests) == len(test_triplets):
            return self.evaluate(request)
        triplet = test_triplets[len(self.tests)]
        h = ["So, you're pretty sure what the rule is now? Cool. I'm going to give you some sets of numbers, and you can tell me whether they seem awesome to you or not.",
             html.P(),
             self.quiz_history(),
             html.Form(method='POST', action='/games/%d/quiz' % self.id,
                       _=["Would you say that %s looks like an awesome triplet? " % triplet,
                          html.submit('Yes', 'yes'),
                          html.submit('No', 'no')])]
        request.reply(h)
    def quiz_history(self):
        return [["You judged %s %s." % (triplet, awesomeness(considered_awesome)),
                 html.Br()]
                for triplet, considered_awesome in zip(test_triplets, self.tests)]
    def evaluate(self, request):
        h1 = [[triplet.display(considered_awesome),
               html.Br()]
              for triplet, considered_awesome in zip(test_triplets, self.tests)]
        terrors = [triplet.quiz(considered_awesome)
                   for triplet, considered_awesome in zip(test_triplets, self.tests)]
        errors = [sum(t) for t in zip(*terrors)]
        if errors[0] == 0:
            h2 = ["Congratulations! You have performed perfectly on this test, having discovered the correct rule: awesome triplets are simply triplets in which each number is greater than the previous one. ",
                  html.P(),
                  "It may surprise you to know this, but in tests carried out by Peter Wason, only 20% of subjects performed as well as you have."]
        else:
            bestscore, besttest = min((ek, k) for k, ek in enumerate(errors))
            if bestscore >= 3:
                h2 = "It looks like you didn't find any rule at all."
            elif besttest == 0:
                h2 = "It looks like you have discovered the correct rule, though you made %d errors." % bestscore
            else:
                if besttest == 1:
                    h2a = "It looks like you thought the rule was that awesome triplets contain numbers which increase by 2."
                elif besttest == 2:
                    h2a = "It looks as though you thought the rule was that awesome triplets contained three successive multiples of the same number, like 3,6,9, or 6,12,18."
                elif besttest == 3:
                    h2a = "It looks as though you thought the rule was that awesome triplets contain numbers separated by the same interval."
                h2a += " In fact, awesome triplets are simply triplets in which each number is greater than the previous one."
                h2 = [h2a,
                      html.P(),
                      "The rule for awesomeness was a fairly simple one, but you invented a more complicated, more specific rule, which happened to fit the first triplet you saw. In experimental tests, it has been found that 80% of subjects do just this, and then never test any of the pairs that *don't* fit their rule. If they did, they would immediately see the more general rule that was applying. This is a case of what psychologists call 'positive bias'. It is one of the many biases, or fundamental errors, which beset the human mind.",
                      html.P(),
                      "There is a thriving community of rationalists at the website ",
                      html.link('http://www.lesswrong.com', "Less Wrong"),
                      " who are working to find ways to correct these fundamental errors. If you'd like to learn how to perform better with the hardware you have, you may want to pay them a visit."]
        h3 = ["If you'd like to learn more about positive bias, you may enjoy the article ",
              html.link('http://www.overcomingbias.com/2007/08/positive-bias-l.html',
                        "'Positive Bias: Look Into the Dark'"),
              html.P(),
              "If you'd like to learn more about the experiment which inspired this test, look for a paper titled 'On the failure to eliminate hypotheses in a conceptual task' (Quarterly Journal of Experimental Psychology, 12: 129-140, 1960)."]
        request.reply([h1, html.P(), h2, html.P(), h3])


if __name__ == '__main__':
    wapp.main(Root())

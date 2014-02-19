class tweeter:
    def __init__(self):
        self.score = 0
        self.tweets = []
        self.userName = ''
        self.userId = 0

class tweet:
    def __init__(self):
        self.text = ''
        self.score = 0
        self.tweetId = 0

class event:
    def __init__(self):
        self.name = ''
        self.id = 0
        self.actors = []
        self.awards = []
        self.winners = []
        self.nominees = []
        self.reporters = []
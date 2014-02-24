class tweeter:
    def __init__(self):
        self.score = 1
        self.tweets = []
        self.userName = ''
        self.userId = 0

class tweet:
    def __init__(self):
        self.text = ''
        self.score = 1
        self.tweetId = 0

class event:
    def __init__(self):
        self.name = ''
        self.id = 0
#        self.actors = []        #Actors list
#        self.awards = []        #Awards list
#        self.winners = []       #Winners list
#        self.nominees = []      #Nominees list
        self.reporters = []     #Top Tweeters list
        self.tags = {}          #Hashtag dict
        self.tagwords = {}      #Keyword dict
        self.words_dict = {}    #Words dict
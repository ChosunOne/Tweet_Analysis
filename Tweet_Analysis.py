print('Loading application dependencies')
import json
import nltk
import operator
import itertools
from collections import OrderedDict

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

def tweetParseLineObjects(json_object, keyword_list, tweeter_list, word_list, user_list):
    twt = tweet()
    twt.text = json_object['text']
    twt.tweetId = json_object['id']

    twter = tweeter()
    twter.tweets.append(twt)
    twter.userName = json_object['user']['screen_name']
    twter.userId = json_object['user']['id']

    text = nltk.wordpunct_tokenize(twt.text)
    
    hashtag = False
    mention = False
    retweet = False

    for word in text:

        if hashtag and (word not in keyword_list):
            keyword_list[word] = 1
            hashtag = False
        if hashtag and (word in keyword_list):
            votes = keyword_list[word]
            keyword_list[word] = votes + 1
            hashtag = False

        if retweet and mention:

                mention = False
                retweet = False

                if word not in user_list:
                    pass
                else:
                    id = user_list[word]
                    mentioned = tweeter_list[id]

                    for t in mentioned.tweets:
                        if t in text:
                            t.score = t.score + 1

                    mentioned.score = mentioned.score + 1


        if '#' in word:
            hashtag = True
        if '@' in word:
            mention = True
        if 'RT' in word:
            retweet = True

        if word not in word_list:
            word_list[word] = 1
        else:
            freq = word_list[word]
            word_list[word] = freq + 1

    if twter.userId not in tweeter_list:
        tweeter_list[twter.userId] = twter
        user_list[twter.userName] = twter.userId
    else:
        tweeter_list[twter.userId].tweets.append(twt)
            
def main():
    file_data = []
    json_data = []
    
    hashtags = {}
    keywords = {}
    words = {}
    tweeters = {}
    userIdTable = {}

    POPULARITY_THRESHOLD = 100
    RETWEET_THRESHOLD = 100
    KEYWORD_THRESHOLD = 10000
    json_file = 'goldenglobes.json'
    print('Loading ', json_file, '...')
    with open(json_file, 'r', encoding="utf8") as f:
        while True:
            line = f.readline()
            if not line: break
            file_data.append(line)
    for x in range(0, len(file_data)):
        try:
            file_data[x].replace('\n', ' n')
            file_data[x].replace('\r', ' r')
            json_data.append(json.loads(file_data[x]))
        except:
            print(x)
            print(file_data[x])
            break

    print('Loading completed.  Processing tweets...')

    progress = 0
    for item in json_data:
        progress = progress + 1
        try:
            tweetParseLineObjects(item, hashtags, tweeters, words, userIdTable)
        except:
            print(item['_id']['$oid'])
            print('An error occurred parsing this line')
            print(item['created_at'])
        if progress % 500 == 0:
                print(progress, ' tweets processed')

    print('Finding keywords')
    for word in words:
        if word in hashtags:
            if word not in keywords:
                keywords[word] = words[word]

    print('Filtering Keywords')
    filtered_keywords = {}
    for keyword in keywords:
        if (keyword != 'RT') and (keyword != '#') and (keyword != '@') and (keyword != 'the') and (keyword != 'is'):
            filtered_keywords[keyword] = keywords[keyword]

    print('Sorting hashtags')
    sorted_hashtags = OrderedDict(sorted(hashtags.items(), key=lambda hashtags: hashtags[1], reverse=True))
    print('Sorting users')
    sorted_users = OrderedDict(sorted(tweeters.items(), key=lambda tweeters: tweeters[1].score, reverse=True))
    print('Sorting keywords')
    sorted_keywords = OrderedDict(sorted(filtered_keywords.items(), key=lambda filtered_keywords: filtered_keywords[1], reverse=True))

    print('Popular Hashtags')

    for word in sorted_hashtags:
        try:
            if hashtags[word] > POPULARITY_THRESHOLD:
                print(word, " ", sorted_hashtags[word])
        except:
            print('Hashtag is unreadable')

    print('Popular Users')

    for user in sorted_users:
        try:
            if sorted_users[user].score > POPULARITY_THRESHOLD:
                print(sorted_users[user].userName, " ", sorted_users[user].score)
        except:
            print('Username is unreadable')

    print('Popular Keywords')

    for word in sorted_keywords:
        try:
            if keywords[word] > KEYWORD_THRESHOLD:
                print(word, " ", sorted_keywords[word])
        except:
            print('Keyword is unreadable')

    print('Popular Retweets')
    i = 0
    for twter in sorted_users:
        if i<10:
            i = i + 1
            try:
                print(sorted_users[twter].userName)
            except:
                print('Username is unreadable')
            for twt in sorted_users[twter].tweets:
                try:
                    print('   ', twt.text)
                except:
                    print('Tweet is unreadable')


main()

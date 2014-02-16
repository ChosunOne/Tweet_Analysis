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

class event:
    def __init__(self):
        self.name = ''
        self.id = 0
        self.actors = []
        self.awards = []
        self.winners = []
        self.nominees = []
        self.reporters = []

# WIP UNTIL NEXT COMMENT
def eventReader(keyword_list, tweeter_list, userId_list):
    """Creates an event that will be reported to the user"""

    awardEvent = event()
    awardEvent.name = keyword_list.first
# WIP COMPLETE

def properNounExtractor(text_dict):
    """Takes a dictionary of words and then returns all the proper nouns in a list"""
    
    print('Building Proper Noun List')
    
    #Proper noun list, progress, and bool
    properNoun_list = []
    properNoun = False
    progress = 0
    total = 0

    #Find the total number of words to be processed
    total = len(text_dict.keys())

    for word in text_dict.keys():
        
        #Create a word list for the tagger
        list = []
        list.append(word)

        #Tag the word
        tag = nltk.pos_tag(list)

        #Check the tag to see if it is a proper noun.  If so, add to proper noun list
        if (tag[0][1] == 'NNP'):
            properNoun = True
        else:
            if properNoun:
                properNoun = False

        if properNoun:
            properNoun_list.append(word)

        #Increment progress
        progress = progress + 1

        #Display progress
        if progress % 50 == 0:
            print(progress, ' out of ', total, ' words processed.')

    return properNoun_list

def properNounMatcher(text_list, properNoun_list):
    """Finds proper nouns in a list of strings and then outputs them to a list separated by '' elements"""

    #Create a list to store the proper nouns in
    extracted_propers = []

    #If the word is in the proper noun list, add it to the extracted list, otherwise just add '' to the list
    for word in text_list:
        if word in properNoun_list:
            extracted_propers.append(word)
        else:
            empty = ''
            extracted_propers.append(empty)

    return extracted_propers

def properNounPhraser(text_list, properNoun_list, phrased_list):
    """Updates a list of phrases of successive proper nouns from a list of strings"""
    
    #Variable to hold the proper noun phrase
    nounHolder = ''

    #Keep adding words to the phrase until we encounter a '', then add phrase to phrase list
    for item in text_list:
        if item == '':
            if nounHolder not in phrased_list:
                phrased_list.append(nounHolder)
            nounHolder = ''
        else:
            nounHolder = nounHolder + ' ' + item

def tweetParseLineObjects(json_object, keyword_list, tweeter_list, word_list, user_list):
    """Parses the tweet from the json_object and updates categories"""

    #Create the tweet object
    twt = tweet()
    twt.text = json_object['text']
    twt.tweetId = json_object['id']

    #Create the tweeter object
    twter = tweeter()
    twter.tweets.append(twt)
    twter.userName = json_object['user']['screen_name']
    twter.userId = json_object['user']['id']

    #Create tokens from text
    text = nltk.wordpunct_tokenize(twt.text)
    
    #Bools
    hashtag = False
    mention = False
    retweet = False
    properNoun = False

    #Look through each word to categorize it
    for word in text:
       
        if hashtag and (word not in keyword_list):
            keyword_list[word] = 1
            hashtag = False
        if hashtag and (word in keyword_list):
            votes = keyword_list[word]
            keyword_list[word] = votes + 1
            hashtag = False

        #Find the original tweet and increase its score. Also find the user and increase his score.
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

        #Interpret the twitter commands and adjust the bools
        if '#' in word:
            hashtag = True
        if '@' in word:
            mention = True
        if 'RT' in word:
            retweet = True

        #Add word to the master word list, or increase its score.
        if word not in word_list:
            word_list[word] = 1
        else:
            freq = word_list[word]
            word_list[word] = freq + 1

    #Add tweeter to the master tweeter list
    if twter.userId not in tweeter_list:
        tweeter_list[twter.userId] = twter
        user_list[twter.userName] = twter.userId
    else:
        tweeter_list[twter.userId].tweets.append(twt)
            
def main():
    #File data variables
    file_data = []
    json_data = []
    
    #Dictionaries
    hashtags = {}
    keywords = {}
    words = {}
    tweeters = {}
    userIdTable = {}

    #Lists
    properNouns = []
    properPhrases = []

    #Number Constants
    POPULARITY_THRESHOLD = 100
    RETWEET_THRESHOLD = 100
    KEYWORD_THRESHOLD = 10000

    #JSON file location
    json_file = 'goldenglobes.json'

    #Start Program
    print('Loading ', json_file, '...')

    #Open the JSON File and load contents into a list
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

    #Parse the text from the tweets
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

    #Pick out keywords from the word list using the hashtags
    print('Finding keywords')
    for word in words:
        if word in hashtags:
            if word not in keywords:
                keywords[word] = words[word]

    #Remove common twitter commands from keyword list
    print('Filtering Keywords')
    filtered_keywords = {}
    for keyword in keywords:
        if (keyword != 'RT') and (keyword != '#') and (keyword != '@') and (keyword != 'the') and (keyword != 'is'):
            filtered_keywords[keyword] = keywords[keyword]
    
    #Sort the dictionaries to display the most popular items
    print('Sorting hashtags')
    sorted_hashtags = OrderedDict(sorted(hashtags.items(), key=lambda hashtags: hashtags[1], reverse=True))
    print('Sorting users')
    sorted_users = OrderedDict(sorted(tweeters.items(), key=lambda tweeters: tweeters[1].score, reverse=True))
    print('Sorting keywords')
    sorted_keywords = OrderedDict(sorted(filtered_keywords.items(), key=lambda filtered_keywords: filtered_keywords[1], reverse=True))

    #Extract the proper nouns from the word list
    properNouns = properNounExtractor(words)

    #Print the most popular hashtags
    print('Popular Hashtags')

    for word in sorted_hashtags:
        try:
            if hashtags[word] > POPULARITY_THRESHOLD:
                print(word, " ", sorted_hashtags[word])
        except:
            print('Hashtag is unreadable')

    #Print the most popular users
    print('Popular Users')

    for user in sorted_users:
        try:
            if sorted_users[user].score > POPULARITY_THRESHOLD:
                print(sorted_users[user].userName, " ", sorted_users[user].score)
        except:
            print('Username is unreadable')

    #Print the most popular users
    print('Popular Keywords')

    for word in sorted_keywords:
        try:
            if keywords[word] > KEYWORD_THRESHOLD:
                print(word, " ", sorted_keywords[word])
        except:
            print('Keyword is unreadable')

    #Print the most popular tweets
    print('Popular Retweets')
    i = 0
    for twter in sorted_users:
        if i<50:
            i = i + 1
            try:
                print(sorted_users[twter].userName)
            except:
                print('Username is unreadable')
            for twt in sorted_users[twter].tweets:
                try:
                    #Find the proper noun phrases
                    protoPhrases = []
                    protoPhrases = properNounMatcher(nltk.wordpunct_tokenize(twt.text), properNouns)
                    properNounPhraser(protoPhrases, properNouns, properPhrases)
                    print('   ', twt.text)
                except:
                    print('Tweet is unreadable')

    #Program is complete
    print('Processing Complete')


main()

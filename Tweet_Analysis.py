print('Loading application dependencies')
import json
import pickle
import nltk
import operator
import itertools
import re
from TweetLibrary import *
from collections import OrderedDict


def keywordCheck(string):
    """Check to see if the word is not a symbol or short word"""
    if ((string != 'RT') 
    and (string != '#') 
    and (string != '@') 
    and (string != 'the') 
    and (string != 'is') 
    and (string != 'I') 
    and (string != 't')
    and (string != '"')
    and (string != 's')
    and (string != 'and')
    and (string != 'in')
    and (string != 'at')
    and (string != 'http')
    and (string != 'it')
    and (string != 'me')
    and (string != 'this')
    and (string != 'my')
    and (string != 'The')
    and (string != 'for')
    and (string != 'like')
    and (string != 'not')
    and (string != 'she')
    and (string != 'an')
    and (string != 'he')):
        return True
    else:
        return False

def createEvent(name, actor_list, award_list, top_tweeter_list, word_list, keyword_list, hashtag_list):
    """Creates an event that will be reported to the user"""

    Event = event()
    Event.name = name
    Event.actors = actor_list
    Event.awards = award_list
    Event.reporters = top_tweeter_list
    Event.words_dict = word_list
    Event.tags = hashtag_list
    Event.tagwords = keyword_list

    return Event

def findAwards(proper_phrase_list):
    award_list = []
    for phrase in proper_phrase_list:
        if 'Best' in phrase:
            award_list.append(phrase)
    return award_list

def findActors(proper_phrase_list):
    actor_list = []
    for phrase in proper_phrase_list:
        tokens = nltk.wordpunct_tokenize(phrase)
        if len(tokens) == 2:
            actor_list.append(phrase)
    return actor_list

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
            #If the word contains multiple words, split them up
            wordList = re.findall('[A-Z][^A-Z]*', word)

            #If there was more than one word, then send each word to proper noun list separately
            for x in range(0, len(wordList)):
                properNoun_list.append(wordList[x])

        #Increment progress
        progress = progress + 1

        #Display progress
        if progress % 1000 == 0:
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

def tweetParseLineObjects(json_object, keyword_list, tweeter_list, word_list, user_list, ghost_list):
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
    recent = False

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

                #If the user mentioned is not in the user list, create a ghost of the user
                if (word not in user_list.keys()) and (word not in ghost_list.keys()):

                    ghosted_twter = tweeter()
                    ghosted_twter.userName = word
                    ghosted_twter.score = 1
                    ghosted_twter.userId = -1

                    ghosted_twt = tweet()
                    ghosted_twt.text = twt.text
                    ghosted_twt.score = 1
                    ghosted_twt.tweetId = -1

                    ghosted_twter.tweets.append(ghosted_twt)

                    ghost_list[word] = ghosted_twter
                    
                    recent = True

                #Check to see if the retweet belongs to a ghost
                if (word in ghost_list) and not recent:
                    exists = False

                    ghost = ghost_list[word]

                    ghosted_twt = tweet()
                    ghosted_twt.text = twt.text

                    for gt in ghost.tweets:
                        if ghosted_twt.text == gt.text:
                            exists = True
                            gt.score = gt.score + 1
                            
                    if exists != True:
                        ghost.tweets.append(ghosted_twt)

                    ghost.score = ghost.score + 1

                #Otherwise, increase the original tweeter's and tweet's score
                if (not recent) and (word in user_list.keys()):
                    id = user_list[word]
                    mentioned = tweeter_list[id]
                    found = False

                    for t in mentioned.tweets:
                        if t.text in twt.text:
                            found = True
                            t.score = t.score + 1

                    if not found:
                        newTweet = tweet()
                        newTweet.text = twt.text
                        mentioned.tweets.append(newTweet)

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

    #Check to see if tweeter has a ghost
    if twter.userName in ghost_list.keys() and not recent:
        

        #Copy the information from the ghost to the tweeter
        ghost = ghost_list[twter.userName]

        for t in ghost.tweets:
            twter.tweets.append(t)

        twter.score = twter.score + ghost.score
        try:
            del ghost_list[twter.userName]
        except KeyError:
            pass

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
    ghosted_tweeters = {}
    userIdTable = {}

    #Lists
    properNouns = []
    properPhrases = []
    top_tweeters = []


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
            tweetParseLineObjects(item, hashtags, tweeters, words, userIdTable, ghosted_tweeters)
        except:
            print(item['_id']['$oid'])
            print('An error occurred parsing this line')
            print(item['created_at'])
        if progress % 2000 == 0:
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
        if keywordCheck(keyword):
            filtered_keywords[keyword] = keywords[keyword]
    
    #Sort the dictionaries to display the most popular items
    print('Sorting hashtags')
    sorted_hashtags = OrderedDict(sorted(hashtags.items(), key=lambda hashtags: hashtags[1], reverse=True))
    print('Sorting users')
    sorted_users = OrderedDict(sorted(tweeters.items(), key=lambda tweeters: tweeters[1].score, reverse=True))
    print('Sorting ghosts')
    sorted_ghosts = OrderedDict(sorted(ghosted_tweeters.items(), key=lambda ghosted_tweeters: ghosted_tweeters[1].score, reverse=True))
    print('Sorting keywords')
    sorted_keywords = OrderedDict(sorted(filtered_keywords.items(), key=lambda filtered_keywords: filtered_keywords[1], reverse=True))

    #Extract the proper nouns from the word list
    properNouns = properNounExtractor(sorted_keywords)

    #Write the most popular hashtags to file
    print('Writing popular hashtags to hashtags.txt')

    with open('hashtags.txt', 'w') as output:
        for word in sorted_hashtags:
            try:
                output.write(word)
                output.write('\r')
            except:
                output.write('Error writing hashtag to file \r')

    #Print the most popular users
    print('Writing users to users.txt')

    with open('users.txt', 'w') as output:
        for user in sorted_users:
            try:
                output.write(sorted_users[user].userName)
                output.write(' ')
                output.write(str(sorted_users[user].score))
                output.write('\r')
            except:
                output.write('Error writing user to file\r')

    #Print the most popular users
    print('Writing keywords to keywords.txt')

    with open('keywords.txt', 'w') as output:
        for word in sorted_keywords.keys():
            try:
                output.write(word)
                output.write(' ')
                output.write(str(keywords[word]))
                output.write('\r')
            except:
                output.write('Error writing keyword to file\r')

    #Print the most popular tweets
    print('Writing retweets to retweets.txt')
    i = 0

    with open('retweets.txt', 'w') as output:
        for twter in sorted_users.values():

            #Find golden globes (DEBUG)
            if twter.userName == 'goldenglobes':
                pass

            i = i + 1
            if i<2500:
                try:
                    if i<20:
                        output.write(twter.userName)
                        output.write('\r')
                except:
                    print('Username is unreadable')
                for twt in twter.tweets:
                    try:
                        #Find the proper noun phrases
                        protoPhrases = []
                        protoPhrases = properNounMatcher(nltk.wordpunct_tokenize(twt.text), properNouns)
                        properNounPhraser(protoPhrases, properNouns, properPhrases)
                        #Only write the top tweets
                        if i<20:
                            output.write('   ')
                            output.write(twt.text)
                            output.write('\r')
                    except:
                        output.write('Error writing tweet to file\r')
            if (i % 500 == 0) and (i <= 2500):
                print(i, ' out of 2500 tweeters processed')

    print('Writing proper noun phrases to proper_phrases.txt')

    with open('proper_phrases.txt', 'w') as output:
        for phrase in properPhrases:
            try:
                output.write(phrase)
                output.write('\r')
            except:
                output.write('Error writing proper noun phrase to file \r')

    print('Finding Awards')

    awards_list = []
    awards_list = findAwards(properPhrases)

    print('Writing discovered awards to awards.txt')

    with open('awards.txt', 'w') as output:
        for award in awards_list:
            try:
                output.write(award)
                output.write('\r')
            except:
                output.write('Error writing award to file \r')

    print('Finding Actors')

    actors_list = []
    actors_list = findActors(properPhrases)

    print('Writing discovered actors to actors.txt')

    with open('actors.txt', 'w') as output:
        for actor in actors_list:
            try:
                output.write(actor)
                output.write('\r')
            except:
                output.write('Error writing actor to file \r')

    for twter in tweeters.values():
        if twter.score > POPULARITY_THRESHOLD:
            top_tweeters.append(twter)

    awardEvent = createEvent('Golden Globes', actors_list, awards_list, top_tweeters, words, keywords, hashtags)

    print('Writing Event to event.txt')

    with open('event.txt', 'wb') as output:
        pickle.dump(awardEvent, output)

    print('Writing Ghost tweets to ghosts.txt')

    with open('ghosts.txt', 'w') as output:
        for g in sorted_ghosts.values():
            try:
                output.write(g.userName)
                output.write('\r')
            except:
                output.write('Error writing username to file\r')
            for t in g.tweets:
                try:
                    output.write('    ')
                    output.write(t.text)
                    output.write('\r')
                except:
                    output.write('Error writing tweet to file\r')

    #Program is complete
    print('Processing Complete')

    return awardEvent


main()

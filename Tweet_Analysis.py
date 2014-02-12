print('Loading application dependencies')
import json
import nltk
import operator
from collections import OrderedDict

def tweetParseLineNLTK(json_object, keyword_list, user_list, word_list):
    tweet = nltk.wordpunct_tokenize(json_object['text'])
    hashtag = False
    mention = False
    for word in tweet:
           
        if hashtag and (word not in keyword_list):
            keyword_list[word] = 1
            hashtag = False
        if hashtag and (word in keyword_list):
            votes = keyword_list[word]
            keyword_list[word] = votes + 1
            hashtag = False

        if mention and (word not in user_list):
            user_list[word] = 1
            mention = False
        if mention and (word in user_list):
            votes = user_list[word]
            user_list[word] = votes + 1
            mention = False

        if '#' in word:
            hashtag = True
        if '@' in word:
            mention = True

        if word not in word_list:
            word_list[word] = 1
        else:
            freq = word_list[word]
            word_list[word] = freq + 1
            
def main():
    file_data = []
    json_data = []
    hashtags = {}
    users = {}
    keywords = {}
    words = {}
    POPULATION_THRESHOLD = 50
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
            tweetParseLineNLTK(item, hashtags, users, words)
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
        tagtup = nltk.tag.str2tuple(keyword)
        tag = tagtup[1]
        if (tag != 'CNJ') and (tag != 'DET') and (tag !='EX') and (tag != 'PRO') and (tag != 'TO'):
            filtered_keywords[keyword] = keywords[keyword]

    print('Sorting hashtags')
    sorted_hashtags = OrderedDict(sorted(hashtags.items(), key=lambda hashtags: hashtags[1]))
    print('Sorting users')
    sorted_users = OrderedDict(sorted(users.items(), key=lambda users: users[1]))
    print('Sorting keywords')
    sorted_keywords = OrderedDict(sorted(filtered_keywords.items(), key=lambda filtered_keywords: filtered_keywords[1]))

    print('Popular Hashtags')

    for word in sorted_hashtags:
        try:
            if hashtags[word] > POPULATION_THRESHOLD:
                print(word, " ", sorted_hashtags[word])
        except:
            print('Hashtag is unreadable')

    print('Popular Users')

    for user in sorted_users:
        try:
            if users[user] > POPULATION_THRESHOLD:
                print(user, " ", sorted_users[user])
        except:
            print('Username is unreadable')

    print('Popular Keywords')

    for word in sorted_keywords:
        try:
            if keywords[word] > 1000:
                print(word, " ", sorted_keywords[word])
        except:
            print('Keyword is unreadable')

main()

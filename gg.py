import json
import nltk
from nltk.tag import pos_tag
import operator
import re
import collections, difflib
import pickle
from TweetLibrary import *

gg = ['Golden Globes', 'GoldenGlobes', 'golden globes']
awardNameStopList = ['at', 'the', 'for']
slangStopList = ["omg", "lol", "ha*ha", "ja.*ja", "na.*na"]
tagger = nltk.data.load(nltk.tag._POS_TAGGER)

def loadJSONFromFile(filePath):
	json_data = []
	with open(filePath, 'r', encoding="utf8") as f:
		for jsonline in f:
			json_data.append(json.loads(jsonline))
	return json_data


def getCategoriesFromFile(filePath):
	awardCategories = []
	with open(filePath, 'r', encoding="utf8") as f:
		awardCategories = [row.rstrip('\n') for row in f]

	return awardCategories

def getEventObject(filePath):
	eventObject = pickle.load( open( "event.txt", "rb" ) )
	return eventObject

def getProperNouns(filePath):
	properNouns =[]
	with open(filePath, 'r',encoding = 'latin-1') as f:
		properNouns = [row.strip('\n') for row in f]
	return properNouns

def findHostTweets(text):
	pattern = re.compile(".* hosting .* Golden Globes .*", re.IGNORECASE)

	hostMentioned = False

	if pattern.match(text):
		hostMentioned = True

	return hostMentioned

def extractProperNouns(tokenizedText):
	# taggedText = pos_tag(tokenizedText)
	taggedText = tagger.tag(tokenizedText)
	grammar = "NP: {<NNP>*}"
	cp = nltk.RegexpParser(grammar)
	chunkedText = cp.parse(taggedText)

	properNouns = []
	for n in chunkedText:
		if isinstance(n, nltk.tree.Tree):               
			if n.label() == 'NP':
				phrase = ""
				for word, pos in n.leaves():
					if len(phrase) == 0:
						phrase = word
					else:
						phrase = phrase + " " + word
				# ignore 'Golden Globes'
				if phrase not in gg:
					properNouns.append(phrase)
	return properNouns

def findHosts(text, possibleHosts):
	if findHostTweets(text):
			tokenizedText = nltk.wordpunct_tokenize(text)
			properNouns = extractProperNouns(tokenizedText)
			for possibleHost in properNouns:
				possibleHosts.append(possibleHost)

	return possibleHosts

def sanitizeTweet(text):
	# remove rewteet
	cleanTweet = re.sub("RT ", "", text)

	# remove links
	if re.match(".*http.*(?= )", cleanTweet):
		cleanTweet = re.sub("http.* ","",cleanTweet)
	else:
		cleanTweet = re.sub("http.*","",cleanTweet)

	# remove @ and #
	symbolsStopList = ["@", "#", "\"", "!", "=", "\.", "\(", "\)", "Golden Globes"]
	for symbol in symbolsStopList:
		cleanTweet = re.sub("%s" % symbol, "", cleanTweet)

	# remove source
	cleanTweet = re.sub("HuffingtonPost", "", cleanTweet)
	cleanTweet = re.sub("GoldenGlobes", "", cleanTweet)

	return cleanTweet

def sanitizeAwardName(text):
	cleanAward = text
	for stopWord in awardNameStopList:
		cleanAward = re.sub("%s " % stopWord, "", cleanAward)

	return cleanAward


def sanitizeTweetForPresenters(text):
	cleanTweet = text

	stopList = ["RT.*:", "@.*", "#.*", "\[.*\]", "\(.*\)"]
	# stopList += slangStopList
	for stopWord in stopList:
		cleanTweet = re.sub("(?i)%s " % stopWord, "", cleanTweet)

	return cleanTweet

def sanitizeSlang(text):
	cleanTweet = text
	stopList = slangStopList
	for stopWord in stopList:
		cleanTweet = re.sub("(?i)%s " % stopWord, "", cleanTweet)

	return cleanTweet


def findPresenters(tweets):
	possiblePresenters = []
	patterns = ["presenting an award", "presenting for best", "presenting best", "presents .* best", "presenting at the", "presents at the", "is presenting"]

	for tweet in tweets:
		text = tweet['text']
		for pattern in patterns:
			rePat = re.compile(".* %s .*" % pattern, re.IGNORECASE)
			if rePat.match(text):
				cleanText = re.search("(?i).*(?=%s)" % pattern, text).group()
				cleanText = sanitizeTweetForPresenters(cleanText)
				if cleanText:
					properNouns = extractProperNouns(nltk.wordpunct_tokenize(cleanText))
					names = []
					for properNoun in properNouns:
						properNoun = sanitizeSlang(properNoun)
						if len(properNoun.split()) >= 2 and not properNoun.isupper():
							names.append(properNoun)
					if names:
						possiblePresenters += names
				break

	data = collections.Counter(possiblePresenters)
	print("List of Presenters:\n========================")
	for presenter in data.most_common():
		print(presenter[0], " (", presenter[1], ")")

	return data.most_common()


def findNominees(tweets):
	count = 0
	patterns = ["will win"]
	for tweet in tweets:
		text = tweet['text']

		for pattern in patterns:
			rePat = re.compile(".* %s .*" % pattern, re.IGNORECASE)
			if rePat.match(text):
				print(text)
				count += 1
	print(count)


def findWinners(tweeters, categories):
	awardResult = {}
	THRESHOLD = 200

	awardPat = re.compile("best .*",re.IGNORECASE)
	winnerPat = re.compile(".*win.*",re.IGNORECASE)
	for twtr in tweeters:
		tweets = twtr.tweets
		for tweet in tweets:
			if winnerPat.match(tweet.text):
				#print("Found winner")
				cleanTweet = sanitizeTweet(tweet.text)
				award = awardPat.search(cleanTweet)
				if award:
					#print("award found")
					properNoun =[]
					firstHalfOfTweet = re.search("(?i).*(?=win)",cleanTweet)
					tokenizedText = nltk.wordpunct_tokenize(firstHalfOfTweet.group())
					'''for word in tokenizedText:
						if word in properNouns:
							properNoun.append(word)
						else:
							properNouns.append(word)
					if len(properNoun) == 0:'''
					properNoun = extractProperNouns(tokenizedText)
					award = sanitizeAwardName(award.group())
					mostSimilarAward = findSimilarCategory(award)
					if mostSimilarAward in awardResult:
						awardResult[mostSimilarAward] +=properNoun
					else:
						awardResult[mostSimilarAward] = properNoun
		THRESHOLD = THRESHOLD -1
		if THRESHOLD<1:
			print("THRESHOLD MET")
			break
	return awardResult

def sanitizeAwardResult(awardResult):
	for a in awardResult:
		tuples = collections.Counter(awardResult[a])
		mostCommon = tuples.most_common()
		print("\n",a,"\n","-------------------","\n",mostCommon[0:5])

def findSimilarCategory(text,awardCategories):
	awardCategories = getCategoriesFromFile('Categories.txt')
	similarities = {}
	for award in awardCategories:
		seq = difflib.SequenceMatcher(a=text.lower(), b=award.lower())
		similarities[award] = seq.ratio()
	mostSimilar = max(similarities.items(), key=operator.itemgetter(1))[0]

	return mostSimilar

def main():
	jsonFile = 'goldenglobes.json'
	eventFile = 'event.txt'
	categoryFile = 'Categories.txt'
	properNounFile = 'proper_phrases.txt'
	tweets = loadJSONFromFile(jsonFile)
	#awardCategories = getCategoriesFromFile(categoryFile)
	eventObject = getEventObject(eventFile)
	properNouns = getProperNouns(properNounFile)

	awardResult = {}#  key is the name of the award, value is the actual winner of the award
	tweeters = eventObject.reporters
	# i = 1
	# for twtr in tweeters:
	# 	print(twtr.userName)
	# 	i = i-1
	# 	if i==0:
	# 		break

	#findNominees(tweets)
	#findPresenters(tweets)
	awardResult = findWinners(tweeters,awardCategories,properNouns)
	sanitizeAwardResult(awardResult)

main()

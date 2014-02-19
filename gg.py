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


def findHostTweets(text):
	pattern = re.compile(".* hosting .* Golden Globes .*", re.IGNORECASE)

	hostMentioned = False

	if pattern.match(text):
		hostMentioned = True

	return hostMentioned



def extractProperNouns(tokenizedText):
	taggedText = pos_tag(tokenizedText)
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


def sanitizeForPresenters(text):
	cleanText = sanitizeTweet(text)
	cleanText = re.sub("(?i)Present", "", cleanText)

	return cleanText

def findPresenterTweets(tweets):
	# pattern = re.compile(".* present.*", re.IGNORECASE)
	# Blah presenting an award 
	# be presenting at GG
	# NNP .* V (presented)

	# 73 tweeters  3583 tweets ...?

	possiblePresenters = []
	patterns = [".*presenter .*", ".* presenting .*", ".* presentation .*", ".* presents .*"]

	for tweet in tweets:
		text = tweet['text']



		for pattern in patterns:
			rePat = re.compile(pattern, re.IGNORECASE)
			if rePat.match(text):
				cleanText = sanitizeForPresenters(text)

				properNouns = extractProperNouns(nltk.wordpunct_tokenize(cleanText))
				names = []
				for properNoun in properNouns:
					if len(properNoun.split()) >= 2 and len(properNoun.split()) < 5:
						if "Best" not in properNoun and "Award" not in properNoun:
							names.append(properNoun)
				if names:
					possiblePresenters += names


	data = collections.Counter(possiblePresenters)
	print(data.most_common())


def findWinners(tweeters, categories):
	awardResult = {}
	awardPat = re.compile("best .*",re.IGNORECASE)
	winnerPat = re.compile(".*win.*",re.IGNORECASE)
	for twtr in tweeters:
		tweets = twtr.tweets
		for tweet in tweets:
			if winnerPat.match(tweet.text):
				cleanTweet = sanitizeTweet(tweet.text)
				properNouns = extractProperNouns(nltk.wordpunct_tokenize(cleanTweet))
				award = awardPat.search(cleanTweet)
				if award:
					award = sanitizeAwardName(award.group())
					mostSimilarAward = findSimilarCategory(award)
					awardResult[mostSimilarAward] = properNouns
	return awardResult

def findSimilarCategory(text):
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
	tweets = loadJSONFromFile(jsonFile)
	awardCategories = getCategoriesFromFile(categoryFile)
	eventObject = getEventObject(eventFile)

	awardResult = {}#  key is the name of the award, value is the actual winner of the award
	tweeters = eventObject.reporters
	for twtr in tweeters:
		print(twtr.userName)

	# findPresenterTweets(tweets)
	# awardResult = findWinners(tweeters,awardCategories)
	
	# for award in awardCategories:
	# 	print(award, "\n===========")
	# 	if award not in awardResult.keys():
	# 		print(None)
	# 	else:
	# 		print(awardResult[award], "\n")

main()

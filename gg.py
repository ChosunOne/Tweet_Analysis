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

'''
def findWinnerTweets(text, categories):
	categoryMentioned = None
	for category in categories:
		pattern = re.compile(".*%s.*" % category, re.IGNORECASE)
		if pattern.match(text):
			categoryMentioned = category
			break

	return categoryMentioned'''


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
'''
def addOrIncrement(dictionary, key):
	if key in dictionary.keys():
		dictionary[key] += 1
	else:
		dictionary[key] = 1

	return dictionary'''


def findHosts(text, possibleHosts):
	if findHostTweets(text):
			tokenizedText = nltk.wordpunct_tokenize(text)
			properNouns = extractProperNouns(tokenizedText)
			for possibleHost in properNouns:
				possibleHosts.append(possibleHost)

	return possibleHosts

'''
def findAwardWinners(text, awardCategories, categoryMentionCount, possibleWinners):
	# ignore retweets
	RTPattern = re.compile("RT.*")
	if not RTPattern.match(text):

		categoryMentioned = findWinnerTweets(text, awardCategories)

		if categoryMentioned:
			categoryMentionCount = addOrIncrement(categoryMentionCount, categoryMentioned)
			if categoryMentionCount[categoryMentioned] > 15:
				awardCategories.remove(categoryMentioned)

			# Remove award name from text
			p = re.compile(re.escape(categoryMentioned), re.IGNORECASE)
			text = p.sub('', text)

			tokenizedText = nltk.wordpunct_tokenize(text)
			properNouns = extractProperNouns(tokenizedText)

			if categoryMentioned not in possibleWinners.keys():
				possibleWinners[categoryMentioned] = properNouns 
			else:
				possibleWinners[categoryMentioned] = possibleWinners[categoryMentioned] + properNouns
	return possibleWinners'''

def printResults(hosts, possibleWinners):
	counter = collections.Counter(hosts)
	hosts = counter.most_common()[0:2]
	print("HOST(S)\n=============\n ", hosts)
	print("\n")
	
	for category in possibleWinners:
		counter = collections.Counter(possibleWinners[category])
		possibleWinners[category] = counter.most_common()[0:2]
		print(category, "\n=============\n ", possibleWinners[category])

	print("\n")

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


def findWinners(tweeter):#(tweeter)
	text = tweet['text']
	sourcePat = re.compile(".*@goldenglobes.*", re.IGNORECASE)
	awardPat = re.compile("best .*", re.IGNORECASE)

	if sourcePat.match(text):	
		pat = re.compile(".* wins .*", re.IGNORECASE)
		# pat = re.compile(".* win.*", re.IGNORECASE)

		if pat.match(text):
			# sanitize
			cleanText = sanitizeTweet(text)
			properNouns = extractProperNouns(nltk.wordpunct_tokenize(cleanText))
			award = awardPat.search(cleanText)
			printAward = ""
			if award:
				printAward = sanitizeAwardName(award.group())

			print(cleanText, "\n",findSimilarCategory(printAward), " - ", properNouns, "\n")

def findWinners(tweeters, categories):
	awardResult = {}
	NUMBER_OF_TWEETER = 40
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
		NUMBER_OF_TWEETER = NUMBER_OF_TWEETER - 1
		if NUMBER_OF_TWEETER<0:
			break;
	return awardResult

def findSimilarCategory(text):
	awardCategories = getCategoriesFromFile('Categories.txt')
	similarities = {}
	for award in awardCategories:
		seq = difflib.SequenceMatcher(a=text.lower(), b=award.lower())
		similarities[award] = seq.ratio()
	mostSimilar = max(similarities.items(), key=operator.itemgetter(1))[0]

	return mostSimilar

'''
def main ():
	jsonFile = 'goldenglobes.json'
	tweets = loadJSONFromFile(jsonFile)
	awardCategories = getCategoriesFromFile('Categories.txt')

	hostCount = 0
	possibleHosts = []

	categoryMentionCount = {}
	possibleWinners = {}

	findSimilarCategory("best drama")

	for tweet in tweets:
		text = tweet['text']

		findWinners(tweet)
		# Find Winners
		# possibleWinners = findAwardWinners(text, awardCategories, categoryMentionCount, possibleWinners)			

		# Find Hosts
		# hosts = findHosts(text, possibleHosts)

		# Find Presenters
		# presenters = findPresenterTweets(text, awardCategories)
		# if presenters:
		# 	print(text)

	# PRINT RESULTS
	# printResults(hosts, possibleWinners)
	'''

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

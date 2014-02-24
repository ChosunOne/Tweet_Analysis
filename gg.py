import json
import nltk
import operator
import re
import collections, difflib
import pickle
from TweetLibrary import *
import time
from collections import OrderedDict

gg = ['Golden Globes', 'GoldenGlobes', 'golden globes']
awardNameStopList = ['at', 'the', 'for']
slangStopList = ["omg", "lol", "ha*ha", "ja.*ja", "na.*na", "wow", "idk", "wtf"]
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
	pattern = re.compile(".* host.* Golden Globes .*", re.IGNORECASE)

	hostMentioned = False

	if pattern.match(text):
		hostMentioned = True

	return hostMentioned

def findHosts(twtrs):
	possibleHosts = {}

	for twtr in twtrs:
		for twt in twtr.tweets:
			text = twt.text
			if findHostTweets(text):
					tokenizedText = nltk.wordpunct_tokenize(text)
					properNouns = extractProperNouns(tokenizedText)
					for possibleHost in properNouns:
						if possibleHost not in possibleHosts.keys():
							possibleHosts[possibleHost] = twtr.score
						else:
							possibleHosts[possibleHost] = possibleHosts[possibleHost] + twtr.score

	sorted_hosts = OrderedDict(sorted(possibleHosts.items(), key=lambda possibleHosts: possibleHosts[1], reverse=True))
	#data = collections.Counter(possibleHosts)
	print("\n\nList of Hosts:\n========================")
	for host in sorted_hosts.keys():
		if sorted_hosts[host] > 60:
			print(host, sorted_hosts[host])

def findPresenters(twtrs):
	possiblePresenters = {}
	patterns = ["presenting an award", "presenting for best", "presenting best", "presents .* best", "presenting at the", "presents at the", "is presenting"]

	for twtr in twtrs:
		for twt in twtr.tweets:
			text = twt.text
			for pattern in patterns:
				rePat = re.compile(".* %s .*" % pattern, re.IGNORECASE)
				if rePat.match(text):
					cleanText = re.search("(?i).*(?=%s)" % pattern, text).group()
					cleanText = sanitizeTweetForPresenters(cleanText)
					if cleanText:
						properNouns = extractProperNouns(nltk.wordpunct_tokenize(cleanText))
						
						for properNoun in properNouns:
							properNoun = sanitizeSlang(properNoun)
							if len(properNoun.split()) >= 2 and not properNoun.isupper():
								if properNoun not in possiblePresenters:
									possiblePresenters[properNoun] = twtr.score
								else:
									possiblePresenters[properNoun] = possiblePresenters[properNoun] + twtr.score
					break

	sorted_presenters = OrderedDict(sorted(possiblePresenters.items(), key=lambda possiblePresenters: possiblePresenters[1], reverse=True))

	print("\n\nList of Presenters:\n========================")
	for presenter in sorted_presenters.keys():
		if sorted_presenters[presenter] > 0:
			print(presenter, sorted_presenters[presenter])


def findNominees(twtrs):
	possibleNominees = {}
	# patterns = ["should have won", "is nominated", "will win .*best", "will win .*award", "hope .*wins"]

	patterns = ["wish .* won","hope .*wins", "is nominated", "will win .* best"]

	for twtr in twtrs:
		for twt in twtr.tweets:
			text = twt.text

			for pattern in patterns:
				rePat = re.compile(".* %s .*" % pattern, re.IGNORECASE)
				if rePat.match(text):
					cleanText = ""
					if re.search("(?i)(?<=hope ).*(?=win)", text):
						cleanText = re.search("(?i)(?<=hope ).*(?=win)", text).group()
					elif re.search("(?i)(?<=wish ).*(?=won)", text):
						cleanText = re.search("(?i)(?<=wish ).*(?=won)", text).group()
					elif re.search("(?i).*(?=%s)" % pattern, text):
						cleanText = re.search("(?i).*(?=%s)" % pattern, text).group()
					else:
						continue

					cleanText = sanitizeTweetForNominees(cleanText)

					properNouns = extractProperNouns(nltk.wordpunct_tokenize(cleanText))
					# print(cleanText, " || ", properNouns, "\n")
					for properNoun in properNouns:
						properNoun = sanitizeSlang(properNoun)
						if properNoun not in possibleNominees:
							possibleNominees[properNoun] = twtr.score
						else:
							possibleNominees[properNoun] = possibleNominees[properNoun] + twtr.score
					break

	sorted_nominees = OrderedDict(sorted(possibleNominees.items(), key=lambda possibleNominees: possibleNominees[1], reverse=True))

	print("\n\nList of Nominees:\n========================")
	for nominee in sorted_nominees.keys():
		if sorted_nominees[nominee] > 0:
			print(nominee, sorted_nominees[nominee])


def findWinners(tweeters, categories):
	awardResult = {}
	THRESHOLD = 200

	awardPat = re.compile("best .*",re.IGNORECASE)
	winnerPat = re.compile(".*win.*",re.IGNORECASE)
	for twtr in tweeters:
		tweets = twtr.tweets
		for tweet in tweets:
			if winnerPat.match(tweet.text):
				cleanTweet = sanitizeTweet(tweet.text)
				award = awardPat.search(cleanTweet)

				if award:
					properNoun =[]
					firstHalfOfTweet = re.search("(?i).*(?=win)",cleanTweet)
					tokenizedText = nltk.wordpunct_tokenize(firstHalfOfTweet.group())

					if tokenizedText:
						properNoun = extractProperNouns(tokenizedText)
						award = sanitizeAwardName(award.group())
						mostSimilarAward = findSimilarCategory(award, categories)
						
						if mostSimilarAward in awardResult:
							awardResult[mostSimilarAward] +=properNoun
						else:
							awardResult[mostSimilarAward] = properNoun
		THRESHOLD = THRESHOLD -1
		if THRESHOLD<1:
			print("THRESHOLD MET")
			break

	sanitizeAwardResult(awardResult)

def findBestWorstDress(tweeters):
	possibleBestDress = []
	possibleWorstDress = []
	bestDressPat = re.compile(".*best dress.*",re.IGNORECASE)
	worstDressPat = re.compile(".*worst dress.*",re.IGNORECASE)
	pat = ""
	for twtr in tweeters:
		for twt in twtr.tweets:
			properNoun =[]
			if bestDressPat.match(twt.text):
				pat = "best"
			elif worstDressPat.match(twt.text):
				pat = "worst"
			else:
				continue
			firstHalfOfTweet = re.search("(?i).*(?=%s)" % pat,twt.text)
			tokenizedText = nltk.wordpunct_tokenize(firstHalfOfTweet.group())

			if tokenizedText:
				properNoun = extractProperNouns(tokenizedText)
				for pn in properNoun:
					if len(pn.split())==2 :
						if pat == 'best':
							possibleBestDress.append(pn)
						else:
							possibleWorstDress.append(pn)

	bestData = collections.Counter(possibleBestDress)
	worstData = collections.Counter(possibleWorstDress)
	print("\n\nList of Best Dressed:\n========================")
	for host in bestData.most_common()[0:5]:
		print(host[0])
	print("\n\nList of Worst Dressed:\n========================")
	for host in worstData.most_common()[0:5]:
		print(host[0])

def extractProperNouns(tokenizedText):
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

	return cleanTweet

def sanitizeAwardName(text):
	cleanAward = text
	for stopWord in awardNameStopList:
		cleanAward = re.sub("%s " % stopWord, "", cleanAward)

	return cleanAward

def sanitizeTweetForPresenters(text):
	cleanTweet = text

	stopList = ["RT.*:", "@.*", "#.*", "\[.*\]", "\(.*\)"]
	for stopWord in stopList:
		cleanTweet = re.sub("(?i)%s " % stopWord, "", cleanTweet)

	return cleanTweet

def sanitizeTweetForNominees(text):
	cleanTweet = text
	words = ["I", "he", "she", "it", "if"]
	stopList = ["RT.*:","@.*: ","@", "#"]
	for stopWord in stopList:
		cleanTweet = re.sub("(?i)%s " % stopWord, "", cleanTweet)

	return cleanTweet

def sanitizeSlang(text):
	cleanTweet = text
	stopList = slangStopList
	for stopWord in stopList:
		cleanTweet = re.sub("(?i)%s " % stopWord, "", cleanTweet)

	return cleanTweet

def sanitizeAwardResult(awardResult):
	for a in awardResult:
		tuples = collections.Counter(awardResult[a])
		mostCommon = tuples.most_common()
		print("\n\n",a,"\n========================\n",mostCommon[0:5])

def findSimilarCategory(text,awardCategories):
	similarities = {}
	for award in awardCategories:
		seq = difflib.SequenceMatcher(a=text.lower(), b=award.lower())
		similarities[award] = seq.ratio()
	mostSimilar = max(similarities.items(), key=operator.itemgetter(1))[0]

	return mostSimilar

def main():
	eventFile = 'event.txt'
	categoryFile = 'Categories.txt'
	awardCategories = getCategoriesFromFile(categoryFile)
	eventObject = getEventObject(eventFile)

	tweeters = eventObject.reporters
	start = time.clock()
	print("\nNumber 1")
	findHosts(tweeters)
	print("\nNumber 2")
	findWinners(tweeters,awardCategories)
	print("\nNumber 3")
	findPresenters(tweeters)
	print("\nNumber 4")
	findNominees(tweeters)
	print("\nNumber 5")
	findBestWorstDress(tweeters)
	end = time.clock()
	print("Total time to run is", (end-start))

main()

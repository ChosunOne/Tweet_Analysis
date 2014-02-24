import json
import nltk
from nltk.tag import pos_tag
import operator
import re
import collections, difflib
import pickle
from TweetLibrary import *
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

	return awardResult

def sanitizeAwardResult(awardResult):
	for a in awardResult:
		tuples = collections.Counter(awardResult[a])
		mostCommon = tuples.most_common()
		print("\n\n",a,"\n========================\n",mostCommon[0:5])

def findSimilarCategory(text,awardCategories):
	# awardCategories = getCategoriesFromFile('Categories.txt')
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
	#tweets = loadJSONFromFile(jsonFile)
	awardCategories = getCategoriesFromFile(categoryFile)
	eventObject = getEventObject(eventFile)

	awardResult = {}#  key is the name of the award, value is the actual winner of the award
	tweeters = eventObject.reporters
	# i = 1
	# for twtr in tweeters:
	# 	print(twtr.userName)
	# 	i = i-1
	# 	if i==0:
	# 		break

	findHosts(tweeters)
	awardResult = findWinners(tweeters, awardCategories)
	findPresenters(tweeters)
	findNominees(tweeters)


main()

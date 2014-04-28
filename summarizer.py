#!/usr/bin/python

from __future__ import division
import sys

#sys.path.append('../beautifulsoup4-4.3.2/build/lib/')
#sys.path.append('../nltk-3.0a3/')
#sys.path.append('../lib/')
#sys.path.append('/usr/local/stow/python/i386_linux22/python-2.6.1/lib/python2.6/site-packages/')

from bs4 import BeautifulSoup
import nltk, operator, re
import bioExtractor, wikiExtractor

# Word index
W = 0
# Tag index
T = 1

# Aliases of the person being queried
names = {}
# Date of Births of the person being queried
dobs = {}
# Place of Births of the person being queried
pobs = {}
# Aliases of the Father of the person being queried
faths = {}
# Aliases of the Mother of the person being queried
moths = {}

#FUNC: Write data to file (Append)
def writeToFile(file_loc, data):
    with open(file_loc, "a") as myfile:
        myfile.write(data)

#FUNC: Return the front part of the file name based on the query.
def getFileFront(query):
    return query.strip().replace(' ', '_') + '_'

#FUNC: Sort the dictionary by values.
def sortDictByValue(dic):
    return sorted(dic.iteritems(), key=operator.itemgetter(1), reverse=True)

#FUNC: Process malformed values.
def procMalVals(mals):
    procs = {}

    vals = mals.keys()
    vals.sort()

    tempVals = mals.keys()
    tempVals.sort(reverse=True)

    while len(vals) != 0:
        val = vals[0]
        count = 0
        for temp in tempVals:
            if val in temp:
                 count += mals[temp]
                 if temp in vals:
                     vals.remove(temp)
        procs[val] = count

    return procs

#FUNC: Print the results for the given collection.
def printResults(coln):
    normed = {}
    for src in coln:
        for val in coln[src]:
            if val in normed:
                normed[val] += 1
            else:
                normed[val] = 1

    # Remove and combine malformed values.
    normed = procMalVals(normed)

    # Normalize the values.
    for val in normed:
        normed[val] = normed[val] / len(coln)

    sortedByVal = sortDictByValue(normed)
    for val in sortedByVal:
        print val[0]

#FUNC: Print all the information extracted from the texts.
def printAllResults():
    print 'Name:'
    printResults(names)
    print '\nDate of Birth'
    printResults(dobs)
    print '\nPlace of Birth'
    printResults(pobs)
    print '\nFather\'s Name:'
    printResults(faths)
    print '\nMother\'s Name:'
    printResults(moths)

#FUNC: Test if the character is a pronunciation character.
def isIPA(word):
    pattern = '[\u0250-\u02AF]+'
    matcher = re.compile(pattern)
    return matcher.match(word)

#FUNC: Check if it is a valid name.
def checkNameValidity(word):
    return word not in ['(', ')', '``', "''"] #and not isIPA(word.encode('utf-8'))

#FUNC: Add to the target list from the source list.
def addToList(t_list, s_list, src):
    val = ' '.join(t_list)
    if val.endswith(','):
        val = val[:-1].strip()
    if src not in s_list:
        s_list[src] = []
    if val and val not in s_list[src]:
        s_list[src].append(val)

#FUNC: Check for the parent (father/mother) of the person being queried.
def checkForParent(tokens, query, parent, src):
    i = 0
    while i < len(tokens):
        if tokens[i][T] == 'PRP$' or any(tokens[i][W] == q + '\'s' for q in query):
            if i < len(tokens) - 2 and tokens[i + 1][W] == parent and tokens[i + 2][W] in ['was', 'is', ',']:
                t_parent = []
                i += 3
                while i < len(tokens) and tokens[i][T] in ['NNP', '``', "''"]:
                    if checkNameValidity(tokens[i][W]):
                        t_parent.append(tokens[i][W])
                    i += 1
                if parent == 'father':
                    addToList(t_parent, faths, src)
                elif parent == 'mother':
                    addToList(t_parent, moths, src)
        i += 1

#FUNC: Check for both the parents of the person being queried for.
def checkForParents(tokens, query, src):
    i = 0
    # Check for father
    checkForParent(tokens, query, 'father', src)
    # Check for mother
    checkForParent(tokens, query, 'mother', src)

#FUNC: Get intersection of two lists, preserving the order of the lists.
def getListIntersection(l1, l2):
    return [val for val in l1 if val in l2]

#FUNC: Check for parameters pertaining to the birth of the person being queried for.
def checkForBirthParams(tokens, query, src):
    birthWords = ['born', 'birth']
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    birthRef = False

    i = 0
    while i < len(tokens):
        if tokens[i][T] == 'NNP' and tokens[i][W] not in months:
            t_name = []
            while i < len(tokens) and tokens[i][T] in ['NNP', '``', "''"] and tokens[i][W] not in months:
                if checkNameValidity(tokens[i][W]):
                    t_name.append(tokens[i][W])
                i += 1
            name = ' '.join(t_name)
            if name and name not in names[src] and len(getListIntersection(t_name, query)) == len(query):
                names[src].append(name)
        if i < len(tokens) - 2 and tokens[i][T] == 'VBD' and tokens[i + 1][W] in birthWords and tokens[i + 2][T] == 'IN':
            birthRef = True
            if tokens[i + 2][W] == 'in':
                t_pob = []
                i += 3
                birthPlaceSet = False
                while i < len(tokens):
                    if tokens[i][T] != 'NNP' and tokens[i][T] != ',':
                        if not birthPlaceSet:
                            i += 1
                        else:
                            break
                    elif tokens[i][T] == 'NNP' or tokens[i][T] == ',':
                        t_pob.append(tokens[i][W])
                        i += 1
                        birthPlaceSet = True
                addToList(t_pob, pobs, src)
                while i != len(tokens) and tokens[i][W] != 'on':
                    i += 1
                if i < len(tokens) and tokens[i][W] == 'on':
                    t_dob = []
                    i += 1
                    while i != len(tokens) and (tokens[i][T] == 'CD' or (tokens[i][T] == 'NNP' and tokens[i][W] in months) or tokens[i][T] == ','):
                        t_dob.append(tokens[i][W])
                        i += 1
                    addToList(t_dob, dobs, src)
            elif tokens[i + 2][W] == 'on':
                t_dob = []
                i += 3
                while i < len(tokens) and (tokens[i][T] == 'CD' or (tokens[i][T] == 'NNP' and tokens[i][W] in months) or tokens[i][T] == ','):
                    t_dob.append(tokens[i][W])
                    i += 1
                addToList(t_dob, dobs, src)
                while i != len(tokens) and tokens[i][W] != 'in':
                    i += 1
                if i < len(tokens) and tokens[i][W] == 'in':
                    t_pob = []
                    i += 1
                    while i != len(tokens) and (tokens[i][T] == 'NNP' or tokens[i][T] == ','):
                        t_pob.append(tokens[i][W])
                        i += 1
                    addToList(t_pob, pobs, src)

        if birthRef and i != len(tokens) and tokens[i][T] == 'TO':
            i += 1
            t_fath = []
            t_moth = []
            while i != len(tokens) and tokens[i][T] in ['NNP', '``', "''"]:
                if checkNameValidity(tokens[i][W]):
                    t_fath.append(tokens[i][W])
                i += 1
            addToList(t_fath, faths, src)

            if i != len(tokens) and tokens[i][W] == 'and' and tokens[i + 1][T] == 'NNP':
                 i += 1
            while i != len(tokens) and tokens[i][T] in ['NNP', '``', "''"]:
                if checkNameValidity(tokens[i][W]):
                    t_moth.append(tokens[i][W])
                i += 1
            addToList(t_moth, moths, src)
            
        i += 1

#FUNC: Extract data from the text.
def extractData(tokens, query, src):
    checkForBirthParams(tokens, query, src)
    checkForParents(tokens, query, src)

#FUNC: Get the PoS tags of the words in the given sentence.
def tagPoS(tokens):
    return nltk.pos_tag(tokens)

#FUNC: Tokenize the given sentence into words.
def tokenize(text):
    return nltk.word_tokenize(text)

#FUNC: Preprocess sentence to cleanse it.
def preprocess(sentence):
    excluded = False
    chars = []
    for char in sentence.strip():
        if char == '[':
            excluded = True
        if not excluded:
            chars.append(char)
        if char == ']':
            excluded = False
    return ''.join(chars)

#FUNC: Extract data from all the text sources.
def extInfoForAllSrcs(query, data):
    for src in data:
        names[src] = [' '.join(query)]
        for para in data[src]:
            sents = para.split('.')
            for sent in sents:
                sent = preprocess(sent)
                if sent:
                    tokens = tokenize(sent)
                    pos = tagPoS(tokens)
                    extractData(pos, query, src)

#FUNC: Get the Wikipedia URL related to the query being made.
def getData(query):
    data = {}
    wikiExt = wikiExtractor.wikiExtractor()
    bioExt = bioExtractor.bioExtractor()

    #tokens = tokenize(query)
    tokens = query
    data['wiki'] = wikiExt.getBio(tokens)
    data['bio'] = bioExt.getBio(tokens)

    return data

#FUNC: Get the input Question from the user.
def getQueryFromConsole():
    if len(sys.argv) < 2:
        sys.exit()
    #query = raw_input('What is your query?: ')
    return sys.argv[1:]

#FUNC: Main method
def main():
    query = getQueryFromConsole()
    data = getData(query)

    extInfoForAllSrcs(query, data)
    printAllResults()

if __name__ == '__main__':
    main()

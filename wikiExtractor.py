import sys

sys.path.append('../beautifulsoup4-4.3.2/build/lib/')

from bs4 import BeautifulSoup
from urllib2 import quote, urlopen
import json

class wikiExtractor:

    #FUNC: Get relevant data from the HTML extracted.
    def getRelevantData(self, html):
        text = []
        parsed = BeautifulSoup(html)
        ps = parsed.findAll('p')
        for p in ps:
            data = p.text.strip()
            if data:
                text.append(data)
        return text

    #FUNC: Fetch page content.
    def fetchPageContent(self, result):
        url = 'http://en.wikipedia.org/wiki/' + result.replace(' ', '_')
        return urlopen(url).read().decode('utf-8')

    #FUNC: Parse the results.
    def parseSearchResult(self, result):
        data = json.loads(result)

        if data.has_key('error'):
            return None
        elif data.has_key('query'):
            query = data['query']
            if query.has_key('search'):
                search = query['search']
                return search[0]['title']

        return None

    #FUNC: Create Wikipedia search query URL.
    def createQueryURL(self, tokens):
        searchQuery = ' '.join(tokens)
        return ('http://en.wikipedia.org/w/api.php?action=query&list=search&srprop=timestamp&format=json&srsearch={}').format(quote(searchQuery))

    #FUNC: Get the JSON search results from the Wikipedia search query.
    def getSearchResults(self, tokens):
        url = self.createQueryURL(tokens)
        return urlopen(url).read()

    #FUNC: Get the biography of the person.
    def getBio(self, tokens):
        result = self.getSearchResults(tokens)
        topResult = self.parseSearchResult(result)
        html = self.fetchPageContent(topResult)
        return self.getRelevantData(html)

    def __init__(self):
        pass

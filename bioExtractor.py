"""
Fetch the biography of a given person from Biography.com
Referred: 1. http://stackoverflow.com/questions/23163120/scraping-biography-com-using-urllib2
          2. https://gist.github.com/zed/07b4b2f5b13507ac33af
"""

import sys

sys.path.append('../beautifulsoup4-4.3.2/build/lib/')

from bs4 import BeautifulSoup
from urllib2 import quote, urlopen
from urlparse import urlsplit, urljoin
import json, posixpath

class bioExtractor:

    #FUNC: Create a Biography.com search query URL.
    def createQueryURL(self, tokens):
        searchQuery = ' '.join(tokens)

        return ('https://www.googleapis.com/customsearch/v1?q={}&'
       'key=AIzaSyCMGfdDaSfjqv5zYoS0mTJnOT3e9MURWkU&'
       'cx=011223861749738482324%3Aijiqp2ioyxw&num=1').format(quote(searchQuery))

    #FUNC: Fetch the JSON data from the webpage.
    def fetchJSON(self, url):
        return json.load(urlopen(url))

    #FUNC: Parse the results.
    def parseResult(self, tokens):
        url = self.createQueryURL(tokens)
        return self.fetchJSON(url)['items'][0]['link']

    #FUNC: Fetch page content.
    def fetchPageContent(self, result):
        slug = posixpath.basename(urlsplit(result).path)
        dataJSON = self.fetchJSON(urljoin('http://api.saymedia-content.com/:apiproxy-anon/content-sites/'
        'cs01a33b78d5c5860e/content-customs/@published/'
        '@by-custom-type/ContentPerson/@by-slug/', slug))
        return dataJSON['entries'][0]['profileTml'].encode('utf-8')

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

    #FUNC: Get the biography of the person.
    def getBio(self, tokens):
        topResult = self.parseResult(tokens)
        html = self.fetchPageContent(topResult)
        return self.getRelevantData(html)

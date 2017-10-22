import pickle
import os  
from datetime import datetime
import asyncio
import async_timeout
import aiohttp
import io
import hashlib
from random import shuffle

API_KEY = 'e9dd4095cf3b493da51bd127641b112c'
SOURCES = ['abc-news-au', 'bbc-news', 'new-scientist']
NEWS_INTERVAL = 4 * 3600
PICKLE_PATH = '/home/pi/python'

class news:
  def __init__(self):
    os.makedirs('cache', exist_ok=True)
    self.loop = asyncio.get_event_loop()
    self.news = {'retrieved': None, 'articles': []}
    if os.path.isfile(PICKLE_PATH + '/news.pickle'):
      with open(PICKLE_PATH + '/news.pickle', 'rb') as f:
        self.news = pickle.load(f)
    self.loop.run_until_complete(self.checknews())

  async def checknews(self):
    if self.news['retrieved']:
      age = (datetime.now() - self.news['retrieved']).seconds
      if (age < NEWS_INTERVAL):
        return
    print('news: checknews() running')
    try:
      articles = await self._doRequest()
    except Exception as exc:
      print('news error', exc)
      return
    self.news['retrieved'] = datetime.now()
    self.news['articles'] = articles
    for article in self.news['articles']:
      article['id'] = hashlib.md5(article['title'].encode()).hexdigest()
    newIds = [x['id'] for x in self.news['articles']]
    for oldId in os.listdir(PICKLE_PATH + '/cache/'):
      if oldId not in newIds:
        os.remove(PICKLE_PATH + '/cache/' + oldId)
    with open(PICKLE_PATH + '/news.pickle', 'wb') as f:
      pickle.dump(self.news, f)

  def numberOf(self):
    return len(self.news['articles'])

  def articles(self):
    return self.news['articles']

  async def getImage(self, articleIndex):
      article = self.news['articles'][articleIndex]
      aid = article['id']
      fname = PICKLE_PATH  + '/cache/' + aid
      if not os.path.isfile(fname):
        url = self.news['articles'][articleIndex]['urlToImage']
        async with aiohttp.ClientSession() as session:
          try:
            with async_timeout.timeout(15, loop=session.loop):
              async with session.get(url) as resp:
                imageData = await resp.read()
                with open(fname, 'wb') as f:
                    f.write(imageData)
          except asyncio.TimeoutError:
            return False
      return fname
    
  async def _doRequest(self):
    params={'sortBy': 'top', 'apiKey': API_KEY}
    articles = []
    for source in SOURCES:
      params['source'] = source
      async with aiohttp.ClientSession() as session:
        try:
          with async_timeout.timeout(15, loop=session.loop):
            async with session.get('https://newsapi.org/v1/articles', params=params) as resp:
              try:
                jnews = await resp.json()
                if 'articles' in jnews:
                  articles.extend(jnews['articles'])
              except Exception as exc:
                print('error reading news source', source)
                print(esc)
        except asyncio.TimeoutError:
          print('time out reading news source', source)
      shuffle(articles)
      return articles

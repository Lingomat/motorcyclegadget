import asyncio
import aiohttp
import pickle
import os  
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import async_timeout
import re

BOMURL = 'http://www.bom.gov.au/places/vic/scoresby/forecast/detailed/'
WEATHER_INTERVAL = 10800
PICKLE_PATH = '/home/pi/python'

class BOMWeather:
  def __init__(self):
    self.bomurl = BOMURL
    self.forecast = {'retrieved': None, 'data': None}
    self.haveData = False
    if os.path.isfile(PICKLE_PATH + '/bom.pickle'):
      with open(PICKLE_PATH + '/bom.pickle', 'rb') as f:
        self.forecast = pickle.load(f)
        self.haveData = True

  async def _fetch(self, session, url):
    try:
      with async_timeout.timeout(15, loop=session.loop):
        async with session.get(url) as response:
          return await response.text()
    except asyncio.TimeoutError:
      return None

  async def update(self):
    doForecast = True
    if self.forecast['retrieved']:
      age = (datetime.now() - self.forecast['retrieved']).seconds
      if age < WEATHER_INTERVAL:
        doForecast = False
    if doForecast:
      async with aiohttp.ClientSession() as session:
        try:
          html = await self._fetch(session, self.bomurl)
        except Exception as exc:
          print('BOM _fetch error', exc)
          return False
        s = html.find('<div id="main-content">')
        e = html.find('<div class="right-column">')
        html = html[s:e]
      if html != None:
        wdata = self.parseTable(html)
        self.forecast = {
          'retrieved': datetime.now(),
          'data': wdata
        }
        self.haveData = True
        with open(PICKLE_PATH + '/bom.pickle', 'wb') as f:
          pickle.dump(self.forecast, f)

  def getIcon(self, obs):
    if obs['d'] < 7 or obs['d'] > 16:
      # night time
      if obs['c'] > 5:
        if obs['r'] > 2:
          return 'showers-night'
        elif obs['r'] > 0:
          return 'light-showers-night'
        else:
          return 'cloudy'
      else:
        if obs['c'] > 0:
          return 'partly-cloudy-night'
        else:
          return 'clear-night'
    else:
      # day time
      if obs['c'] > 5:
        #likelyh to rain
        if obs['r'] > 4:
          #showers
          return 'rain'
        elif obs['r'] > 2:
          return 'light-showers'
        else:
          #light
          return 'cloudy'
      else:
        # otherwise, clear... is it actually sunny (UV) and warm?
        if obs['u'] > 3 and obs['t'] > 14:
          # yep!
          return 'motorcycle'
        elif obs['c'] > 0:
          return 'partly-cloudy'
        else:
          return 'sunny'

  def getRows(self, element, selector):
    row = element.find("th", text=re.compile(selector))
    vals = []
    parent = row.find_parent("tr")
    for column in parent.findAll("td"):
      tstr = column.string.replace('%', '')
      try:
        x = int(tstr)
        vals.append(x)
      except ValueError:
        vals.append(0)
    return vals

  def parseTable(self, html):
    soup = BeautifulSoup(html, "lxml")
    wd = []
    days = soup.findAll('div', attrs={'class':'forecast-day'}, limit=2)
    for day in days:
      thisdate = datetime.strptime(day['id'], 'd%Y-%m-%d')
      rdata = self.getRows(day, "10% chance")
      tdata = self.getRows(day, "Air temperature")
      udata = self.getRows(day, "UV Index")
      hdata = self.getRows(day, "Relative humidity")
      cdata = self.getRows(day, "Chance of any rain")
      for t in range(0,8):
        th = (t * 3) + 1
        sdate = datetime(thisdate.year, thisdate.month, thisdate.day, th)
        edate = sdate + timedelta(hours=3)
        if (datetime.now() < edate):
          thisobs = {
            'd': th,
            'r': rdata[t],
            't': tdata[t],
            'u': udata[t],
            'c': cdata[t],
            'h': hdata[t]
          }
          thisobs['i'] = self.getIcon(thisobs)
          wd.append(thisobs)
    return wd

  def getIconPath(self, iconid):
    return PICKLE_PATH + '/bomicons/' + iconid + '.png'

  def getForecast(self):
    return self.forecast['data']

async def main(loop):
  weather = BOMWeather()
  await weather.update()

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(main(event_loop))
    finally:
        event_loop.close()
    


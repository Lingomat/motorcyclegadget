import RPi.GPIO as GPIO
import lcd
import time
#import Adafruit_DHT
import asyncio
import news
import bom
import htu21d
import sys

S_BAR_HEIGHT = 24
S_FONT_SIZE = 20

D_FONT_SIZE = 18
H_FONT_SIZE = 20
B_FONT_SIZE = 28
W_FONT_SIZE = 31
G_FONT_SIZE = 15
PAGE_DURATION = 7
TIMEOUT = 60

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18,1)

#sensor = Adafruit_DHT.AM2302

print('init lcd')
tft = lcd.pitft()
print('init news')
newz = news.news()
print('init weather')
bom = bom.BOMWeather()
dfont = tft.font(D_FONT_SIZE, 'dejavu', 'DejaVuSans')
sfont = tft.font(S_FONT_SIZE, 'dejavu', 'DejaVuSans')
hfont = tft.font(H_FONT_SIZE, 'droid', 'DroidSans')
bfont = tft.font(B_FONT_SIZE, 'droid', 'DroidSerif-Regular')
wfont = tft.font(W_FONT_SIZE, 'dejavu', 'DejaVuSans-Bold')
gfont = tft.font(G_FONT_SIZE, 'dejavu', 'DejaVuSansMono')

sleepmode = False

async def drawTemp(sensor):
  #(humid, temp) = Adafruit_DHT.read_retry(sensor, 22)
  (temp, humid) = await sensor.getValues()
  tft.rect(0, 320 - S_BAR_HEIGHT, 240, S_BAR_HEIGHT, (0,0,100))
  if temp == None:
    tstr = '?'
  else:
    tstr = str(round(temp,1))+'C'
  if humid == None:
    hstr = '?'
  else:
    hstr = str(round(humid,1))+'%'
  tmstr = time.strftime('%H:%M')
  ypos = 320 - S_BAR_HEIGHT + 1
  tft.text(sfont, tstr, 3, ypos)
  tft.ctext(sfont, tmstr, ypos)
  tft.rtext(sfont,hstr, ypos, 3)
  tft.update()

async def drawNews(index):
  tft.rect(0, 0, 240, 320 - S_BAR_HEIGHT, (100,0,0)) # blank all but sensor bar
  headheight = ((H_FONT_SIZE + 4) * 3) # 3 lines
  try:
    image = await newz.getImage(index)
  except Exception as exc:
    print('image fetch error', exc)
    return
  imageRect = (0, headheight, 240, 320 - headheight - S_BAR_HEIGHT)
  if image != False:
    tft.dispZoomImage(image, imageRect)
  text = newz.articles()[index]['title']
  while text:
    tft.rect(0, 0, 240, headheight, (120,0,0))
    text = tft.wtext(text, (255,255,255), (0,0,240,headheight), hfont, True)
    tft.update()
    await asyncio.sleep(PAGE_DURATION)

async def drawForecast(weatherdata, ypos):
  columnwidth = 60
  iconheight = 60
  tempheight = 40
  rainheight = 22
  timeheight = 25
  totalheight = iconheight + (tempheight + rainheight + timeheight)
  for i in range(0,3):
    tft.line((0,ypos + i*totalheight),(239,ypos + i*totalheight))
  for i in range(0,5):
    xp = i * columnwidth
    if i == 4:
      xp = xp - 1
    tft.line((xp, ypos),(xp,ypos + 2 * totalheight))
  for i in range(0,8):
    w = weatherdata[i]
    icon = bom.getIconPath(w['i'])
    if w['c'] > 5:
      rain = str(w['r'])+'mm'
    else:
      rain = '-'
    tstr =  str(w['d']) + ':00'
    yoff = 0 if i < 4 else totalheight
    xpos = ((i % 4) * columnwidth)
    tft.dispZoomImage(icon, (xpos, ypos + yoff, columnwidth, iconheight))
    tft.btext(wfont, str(w['t']), (xpos, ypos + iconheight + yoff, columnwidth, tempheight), 'top')
    tft.btext(gfont, rain, (xpos, ypos + iconheight + tempheight + yoff, columnwidth, rainheight))
    tft.btext(dfont, tstr, (xpos, ypos + iconheight + tempheight + rainheight + yoff, columnwidth, timeheight), 'bottom')

async def displayWeather():
  try:
    await bom.update()
  except Exception as exc:
    print(exc)
  tft.rect(0, 0, 240, 320 - S_BAR_HEIGHT, (0,120,0))
  if bom.haveData:
    try:
      await drawForecast(bom.getForecast(), 0)
    except Exception as exc:
      print(exc)
      exit()
  else:
    tft.ctext(sfont, 'No weather data!', 100)
  tft.update()
  await asyncio.sleep(PAGE_DURATION)

async def monitorMotion():
  def sleep_begin():
    GPIO.output(18,0)
  def sleep_end():
    GPIO.output(18,1)
  global sleepmode
  lastalive = time.time()
  lastmotion = 0
  while True:
    motion = GPIO.input(16)
    if motion != lastmotion:
      lastmotion = motion
    if motion:
      if sleepmode:
        sleep_end()
        sleepmode = False
      lastalive = time.time()
    elif not sleepmode:
      if time.time() - lastalive > TIMEOUT:
        sleep_begin()
        sleepmode = True
    await asyncio.sleep(0.5)   

async def main(loop):
  global sleepmode
  print('init HTU21D')
  sensor = htu21d.HTU21D(loop)
  #asyncio.ensure_future(monitorMotion())
  i = 0
  while True:
    if not sleepmode:
      await drawTemp(sensor)
      await drawNews(i)
      await displayWeather()
      i = i + 1
      if i == newz.numberOf():
        i = 0
        try:
          await newz.checknews()
        except Exception as exc:
          print(exc)
          exit()
    else:
      await asyncio.sleep(0.5)    

if __name__ == '__main__':
  event_loop = asyncio.get_event_loop()
  tasks = [
    asyncio.ensure_future(main(event_loop)),
    asyncio.ensure_future(monitorMotion())
  ]
  print('starting event loop')
  event_loop.run_until_complete(asyncio.wait(tasks))
  #event_loop.close()


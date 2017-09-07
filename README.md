# motorcyclegadget
News/weather/motorcycle status gadget runs on a Raspberry Pi Zero W with a 240x320 LCD display available as a framebuffer (fb1)
Uses an I2C htu21 temp/humid sensor and a generic PIR motion detector on GPIO

Entry point is gadget.py which must be run invoked with sudo for pygame access to fb1 (even if you add fb1 to the user, shrug)

Python async is hopelessly designed and a huge pain in the arse. There's a lot of try: except: handling just to
view any errors in co-routines.

# dependencies
python 3.5+ for async await (to avoid compiling from source, get https://github.com/jjhelmus/berryconda)
pygame (needs to be compiled from source)
RPi.GPIO (pip)
aiohttp (pip)
BeautifulSoup 4 (pip)
lxml (pip and I think some apt-get on dependencies?)

# data sources

Uses newsapi.org for the news. Images are cached in a cache/
Scrapes an Aussie BOM HTML page because the BOM doesn't offer the hourly forecast data via any actual API. ;-/
Uses weather icons thieved from weather api, uses some logic on weather to indicate motorcycling weather.

Should all be pretty self explanitory from the source.

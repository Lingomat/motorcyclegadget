import io, fcntl 
import struct
import array
import time
import asyncio

I2C_SLAVE=0x0703 
HTU21D_ADDR = 0x40
CMD_READ_TEMP_HOLD = b"\xE3"
CMD_READ_HUM_HOLD = b"\xE5"
CMD_READ_TEMP_NOHOLD = b"\xF3"
CMD_READ_HUM_NOHOLD = b"\xF5"
CMD_WRITE_USER_REG = b"\xE6"
CMD_READ_USER_REG = b"\xE7"
CMD_SOFT_RESET = b"\xFE"

class i2c(object):
   def __init__(self, device, bus):
      self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
      self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)
      # set device address
      fcntl.ioctl(self.fr, I2C_SLAVE, device)
      fcntl.ioctl(self.fw, I2C_SLAVE, device)
   def write(self, bytes):
      self.fw.write(bytes)
   def read(self, bytes):
      return self.fr.read(bytes)
   def close(self):
      self.fw.close()
      self.fr.close()

class HTU21D(object):
    def __init__(self, loop):
        self.loop = loop
        self.dev = i2c(HTU21D_ADDR, 1)  # HTU21D 0x40, bus 1
        self.dev.write(CMD_SOFT_RESET)  # Soft reset
        time.sleep(.1)

    def ctemp(self, sensor_temp):
        t_sensor_temp = sensor_temp / 65536.0
        return -46.85 + (175.72 * t_sensor_temp)

    def chumid(self, sensor_humid):
        t_sensor_humid = sensor_humid / 65536.0
        return -6.0 + (125.0 * t_sensor_humid)

    def temp_coefficient(self, rh_actual, temp_actual, coefficient=-0.15):
        return rh_actual + (25 - temp_actual) * coefficient

    def crc8check(self, value):
        # Ported from Sparkfun Arduino HTU21D Library:
        # https://github.com/sparkfun/HTU21D_Breakout
        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]

        # POLYNOMIAL = 0x0131 = x^8 + x^5 + x^4 + 1 divisor =
        # 0x988000 is the 0x0131 polynomial shifted to farthest
        # left of three bytes
        divisor = 0x988000

        for i in range(0, 16):
            if(remainder & 1 << (23 - i)):
                remainder ^= divisor
            divisor = divisor >> 1

        if remainder == 0:
            return True
        else:
            return False

    async def read_temperature(self):
        self.dev.write(CMD_READ_TEMP_NOHOLD)  # Measure temp
        #time.sleep(.1)
        await asyncio.sleep(.1, loop=self.loop)
        data = self.dev.read(3)
        buf = array.array('B', data)
        if self.crc8check(buf):
          temp = (buf[0] << 8 | buf[1]) & 0xFFFC
          return self.ctemp(temp)
        else:
          return None

    async def read_humidity(self):
      temp_actual = await self.read_temperature()  # For temperature coefficient compensation
      self.dev.write(CMD_READ_HUM_NOHOLD)  # Measure humidity
      #time.sleep(.1)
      await asyncio.sleep(.1, loop=self.loop)
      data = self.dev.read(3)
      buf = array.array('B', data)
      if self.crc8check(buf):
        humid = (buf[0] << 8 | buf[1]) & 0xFFFC
        rh_actual = self.chumid(humid)
        rh_final = self.temp_coefficient(rh_actual, temp_actual)
        rh_final = 100.0 if rh_final > 100 else rh_final  # Clamp > 100
        rh_final = 0.0 if rh_final < 0 else rh_final  # Clamp < 0
        return rh_final
      else:
        return None

    async def getValues(self):
      temp_actual = await self.read_temperature()  # For temperature coefficient compensation
      if temp_actual == None:
        return (None, None)
      self.dev.write(CMD_READ_HUM_NOHOLD)  # Measure humidity
      #time.sleep(.1)
      await asyncio.sleep(.1, loop=self.loop)
      data = self.dev.read(3)
      buf = array.array('B', data)
      if self.crc8check(buf):
        humid = (buf[0] << 8 | buf[1]) & 0xFFFC
        rh_actual = self.chumid(humid)
        rh_final = self.temp_coefficient(rh_actual, temp_actual)
        rh_final = 100.0 if rh_final > 100 else rh_final  # Clamp > 100
        rh_final = 0.0 if rh_final < 0 else rh_final  # Clamp < 0
      else:
        rh_final = None
      return (temp_actual, rh_final)

if __name__ == "__main__":
    obj = HTU21D()
    print("Temp: %s C" % obj.read_temperature())
    print("Humid: %s %% rH" % obj.read_humidity())
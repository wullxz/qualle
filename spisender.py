#!/usr/bin/env python

import spidev
import time
from threading import Thread, Event

class SPISender(Thread):

  def __init__(self, speed=5000):
    Thread.__init__(self)
    self.speed = speed
    self.data = [0x0, 0x0]
    self.spi = spidev.SpiDev()
    self.spi.open(0, 0)
    self.spi.mode = 0
    self.spi.max_speed_hz=(self.speed)
    self.stop = Event()
    print("Clock speed: " + str(self.spi.max_speed_hz))

  def write(self):
    self.spi.xfer2(self.data, self.speed)

  def run(self):
    while not self.stop.isSet():
      self.write()
      time.sleep(1)

  def setData(self, data):
    self.data = data

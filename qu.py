#!/usr/bin/env python

import pygame
import time
import sys
import threading
import struct
import spidev
import RPi.GPIO as GPIO
import os
from config import Config
from pygame.locals import *
from timerreset import TimerReset
from pprint import pprint as pp


CS=26
LEDON=0
LEDOFF=1
CLEDON=1
CLEDOFF=0

class Qualle(object):

  def __init__(self):
    print("Setting up the QUALLE!")
    pygame.init()
    self.img={}
    self.led={}
    self.spichan1 = {}
    self.spichan2 = {}
    self.colorled = {}
    self.colorpins = []
    self.datapath = "/home/pi/Desktop/qualle/"
    self.cfg = Config()
    self.debug = self.cfg.raw.getboolean("General", "debug")
    dinfo = pygame.display.Info()
    # don't go fullscreen if debug is enabled
    if self.debug:
      #TODO: uncomment in production
      self.dimension = (800, 600) #(dinfo.current_w, dinfo.current_h)
      pygame.display.set_mode(self.dimension)#, FULLSCREEN)
    else:
      self.dimension = (dinfo.current_w, dinfo.current_h)
      pygame.display.set_mode(self.dimension, FULLSCREEN)
    self.surface = pygame.display.get_surface()
    # show loading screen
    pygame.mouse.set_visible(False)
    self.surface.fill((0, 0, 0))
    loading = pygame.image.load("/home/pi/qualle/loading.jpg")
    hoffset = self.dimension[0] / 2
    hoffset = hoffset - (loading.get_rect().width / 2)
    voffset = self.dimension[1] / 2
    voffset = voffset - (loading.get_rect().height / 2)
    self.surface.blit(loading, (hoffset, voffset))
    pygame.display.update()
    self.waitTime = int(self.cfg.General['waittime'])
    print("Setting up the timer for %d seconds!" % self.waitTime)
    self.timer = TimerReset(self.waitTime, self.resetScreen)
    self.timer.start()
    self.spi = spidev.SpiDev()
    self.spi.open(0, 0)
    self.setUpListener()
    self.initPics()
    GPIO.output(CS, 1) # prepare spi cs
    print("Done setting up the QUALLE!")

  def sendSPI(self, data):
    GPIO.output(CS, 0)
    self.spi.writebytes(data)
    GPIO.output(CS, 1)


  def initPics(self):
    # load pictures
    pp(self.cfg.Pictures)
    self.img['default'] = self.loadImg(os.path.join(self.datapath, self.cfg.Pictures['default']))
    for t, k in self.cfg.Taster.iteritems():
      k = int(k)
      print("Setting picture for taster %s with pin value %s" % (t, k))
      path = os.path.join(self.datapath, self.cfg.Pictures[t])
      self.img[k] = self.loadImg(path)

  def loadImg(self, path):
    image = pygame.image.load(path)
    image = pygame.transform.scale(image, self.dimension)
    return image

  def run(self):
    self.resetScreen()
    # main event loop: this keeps the program running
    while True:
      for event in pygame.event.get():
        if event.type == QUIT:
          self.quit()
        if event.type == KEYDOWN and event.key == K_q:
          self.quit()

  def setUpListener(self):
    GPIO.setmode(GPIO.BOARD)
    # set chip select
    GPIO.setup(CS, GPIO.OUT)
    # set up buttons, leds and spi
    for k, v in self.cfg.Taster.iteritems():
      # set up buttons and button leds
      v = int(v)
      GPIO.setup(v, GPIO.IN)
      self.led[v] = int(self.cfg.TasterLED[k])
      GPIO.setup(self.led[v], GPIO.OUT)
      GPIO.add_event_detect(v, GPIO.FALLING, callback=self.btn_handler, bouncetime=300)
      # set up spi values
      self.spichan1[v] = self.calcSPIOutput(1, self.cfg.SPIChan1[k])
      self.spichan2[v] = self.calcSPIOutput(0, self.cfg.SPIChan2[k])
      btns=self.cfg.QualleColors[k].split(";")
      pins=[]
      for b in btns:
        if b != "":
          pin = int(self.cfg.ColorLED[b])
          pins.append(pin)
      self.colorled[v] = pins
    # color leds
    for k, v in self.cfg.ColorLED.iteritems():
      v = int(v)
      GPIO.setup(v, GPIO.OUT)
      self.colorpins.append(v)
    pp(self.led)

  def quit(self):
    self.timer.quit()
    GPIO.cleanup()
    pygame.quit()
    sys.exit()

  def btn_handler(self, channel):
    self.timer.cancel()
    # button press
    if not GPIO.input(channel):
      print("Button press detected: " + str(channel))
      data1 = self.spichan1[channel] # [ ord(c) for c in struct.pack("!I", self.spichan1[channel]) ]
      data2 = self.spichan2[channel]
      print("chan 1: " + str(data1))
      print("chan 2: " + str(data2))
      self.sendSPI(data1)
      self.sendSPI(data2)
      for color in self.colorpins:
        if color not in self.colorled[channel]:
          GPIO.output(color, CLEDOFF)
        else:
          GPIO.output(color, CLEDON)
      for k,l in self.led.iteritems():
        if channel != k:
          GPIO.output(l, LEDOFF)
      GPIO.output(self.led[channel], LEDON)
      self.surface.fill((0, 0, 0))
      self.surface.blit(self.img[channel], (0, 0))
      pygame.display.update()
    self.timer.restart()

  def resetScreen(self):
    for k,l in self.led.iteritems():
      GPIO.output(l, LEDOFF)
    for p in self.colorpins:
      GPIO.output(p, CLEDOFF)
    if self.cfg.General['spichan1idle'] != -1:
      spi1 = self.calcSPIOutput(1, self.cfg.General['spichan1idle'])
      self.sendSPI(spi1)
    if self.cfg.General['spichan2idle'] != -1:
      spi2 = self.calcSPIOutput(0, self.cfg.General['spichan2idle'])
      self.sendSPI(spi2)
    self.surface.fill((0, 0, 0))
    self.surface.blit(self.img['default'], (0, 0))
    pygame.display.update()

  def calcSPIOutput(self, chan, value):
    value = int(value)
    val1 = 0b00010000
    val2 = 0b00000000
    chan = chan << 7
    val1 = val1 | chan
    # make sure, limit's not overdone
    limit = int(self.cfg.General['spilimit'])
    if value > limit:
      value = limit
    # assemble first byte
    tmp = value >> 6
    val1 = tmp | val1
    # assemble 2nd byte
    tmp = value << 2
    tmp = tmp & 0b11111111 # limit to 1 byte
    val2 = tmp
    return [val1, val2]


if __name__ == "__main__":
  qualle = Qualle()
  qualle.run()

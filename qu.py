#!/usr/bin/env python

import pygame
import time
import sys
import threading
import struct
import RPi.GPIO as GPIO
from spisender import SPISender
from pygame.locals import *
from timerreset import TimerReset

waitTime=10

T1=38
T2=36
MOSI=19
LEDON=0
LEDOFF=1
debug=True

class Qualle(object):

  def __init__(self):
    print("Setting up the QUALLE!")
    pygame.init()
    self.img={}
    self.led={}
    self.spichan1 = {}
    self.spichan2 = {}
    dinfo = pygame.display.Info()
    if debug:
      #TODO: uncomment in production
      self.dimension = (800, 600) #(dinfo.current_w, dinfo.current_h)
      pygame.display.set_mode(self.dimension)#, FULLSCREEN)
    else:
      self.dimension = (dinfo.current_w, dinfo.current_h)
      pygame.display.set_mode(self.dimension, FULLSCREEN)
    self.surface = pygame.display.get_surface()
    print("Setting up the timer for %d seconds!" % waitTime)
    self.timer = TimerReset(waitTime, self.resetScreen)
    self.timer.start()
    self.setUpListener()
    self.initPics()
    self.spisender = SPISender()
    self.spisender.start()
    self.spichan1[T1] = [0b1001001, 0b11110000]
    self.spichan2[T1] = 4096 | 256
    self.spichan1[T2] = [0b1001000, 0b00100000]
    self.spichan2[T2] = 4096 | 512
    print("Done setting up the QUALLE!")

  def initPics(self):
    # load pictures
    self.img['start'] = self.loadImg("start.jpg")
    self.img[T1] = self.loadImg('b1.jpg')
    self.img[T2] = self.loadImg('b2.jpg')

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
    GPIO.setup(T1, GPIO.IN)
    GPIO.setup(T2, GPIO.IN)
    # define LEDs
    self.led[T1] = 40
    self.led[T2] = 37

    for k,l in self.led.iteritems():
      GPIO.setup(l, GPIO.OUT)

    GPIO.add_event_detect(T1, GPIO.FALLING, callback=self.btn_handler, bouncetime=300)
    GPIO.add_event_detect(T2, GPIO.FALLING, callback=self.btn_handler, bouncetime=300)

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
      data = self.spichan1[channel] # [ ord(c) for c in struct.pack("!I", self.spichan1[channel]) ]
      print(data)
      self.spisender.setData(data)
      for k,l in self.led.iteritems():
        if channel != k:
          GPIO.output(l, LEDOFF)
      GPIO.output(self.led[channel], LEDON)
      self.surface.blit(self.img[channel], (0, 0))
      pygame.display.update()
    self.timer.restart()

  def resetScreen(self):
    for k,l in self.led.iteritems():
      GPIO.output(l, LEDOFF)
    self.surface.blit(self.img['start'], (0, 0))
    pygame.display.update()


if __name__ == "__main__":
  qualle = Qualle()
  qualle.run()

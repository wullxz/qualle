#!/usr/bin/env python

import pygame
import time
import sys
import threading
import RPi.GPIO as GPIO
from pygame.locals import *

waitTime=5

img={}
led={}
T1=38
T2=36
dim=(0, 0) # dimensions of screen; initialized in init()
zero=(0, 0) # zero position
LEDON=0
LEDOFF=1
active=0

def init():
  global dim
  dinfo = pygame.display.Info()
  dim = (dinfo.current_w, dinfo.current_h)
  pygame.display.set_mode(dim, FULLSCREEN)
  # load pictures
  img['start'] = loadImg("start.jpg")
  img[T1] = loadImg('b1.jpg')
  img[T2] = loadImg('b2.jpg')
  display = pygame.display.get_surface()
  display.blit(img['start'], zero)
  pygame.display.update()

def loadImg(path):
  image = pygame.image.load(path)
  image = pygame.transform.scale(image, dim)
  return image

def main():
  pygame.init()
  print("Setting up buttons...")
  setUpListener()
  print("Done setting up buttons!")
  init()
  # main event loop: this keeps the program running
  while True:
    for event in pygame.event.get():
      if event.type == QUIT:
        cleanup()
        quit()
      if event.type == KEYDOWN and event.key == K_q:
        cleanup()
        quit()

def setUpListener():
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(T1, GPIO.IN)
  GPIO.setup(T2, GPIO.IN)

  # define LEDs
  led[T1] = 40
  led[T2] = 37

  for k,l in led.iteritems():
    GPIO.setup(l, GPIO.OUT)

  GPIO.add_event_detect(T1, GPIO.FALLING, callback=btn_handler, bouncetime=300)
  GPIO.add_event_detect(T2, GPIO.FALLING, callback=btn_handler, bouncetime=300)

def cleanup():
  GPIO.cleanup()

def quit():
  pygame.quit()
  sys.exit()
  return

def btn_handler(channel):
  global active
  if active == channel:
    # don't do anything when pic is already displayed
    return
  else:
    active = channel
    timer = Timeout()
    timer.cancel()
    display = pygame.display.get_surface()
    # button press
    if not GPIO.input(channel):
      print("Button press detected: " + str(channel))
      for k,l in led.iteritems():
        if channel != k:
          GPIO.output(l, LEDOFF)
      GPIO.output(led[channel], LEDON)
      display.blit(img[channel], zero)
      pygame.display.update()
      timer.start()

def resetScreen():
  global active
  active = 0
  for k,l in led.iteritems():
    GPIO.output(l, LEDOFF)
  display = pygame.display.get_surface()
  display.blit(img['start'], zero)
  pygame.display.update()

# Singleton class for global timer
class Timeout(object):
  timer = None
  _instance = None

  def start(self):
    if self.timer != None:
      print("Restarting timer...\n")
      try:
        self.cancel()
      except:
        pass
    print(self.timer)
    print("Starting timer!\n")
    self.timer = None
    self.timer=threading.Timer(waitTime, resetScreen)
    self.timer.start()

  def cancel(self):
    print("Canceling timer!")
    if self.timer != None:
      try:
        self.timer.cancel()
      except:
        pass

  def __new__(cls, *args, **kwargs):
    if not cls._instance:
      cls._instance = super(Timeout, cls).__new__(cls, *args, **kwargs)
    return cls._instance

class NonsenseException(Exception):
  pass

if __name__ == "__main__":
  try:
    main()
  except NonsenseException:
    pass
  finally:
    cleanup()


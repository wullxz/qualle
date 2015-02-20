#!/usr/bin/env python

import pygame
import time
import sys
import threading
import RPi.GPIO as GPIO
from pygame.locals import *

waitTime=10

img={}
T1=38
T2=36
dim=(0, 0) # dimensions of screen; initialized in init()
zero=(0, 0) # zero position

def init():
  dinfo = pygame.display.Info()
  dim = (dinfo.current_w, dinfo.current_h)
  pygame.display.set_mode(dim, FULLSCREEN)
  img['start'] = pygame.image.load("start.jpg")
  img[T1] = pygame.image.load('b1.jpg')
  img[T2] = pygame.image.load('b2.jpg')
  display = pygame.display.get_surface()
  display.blit(img['start'], zero)
  pygame.display.update()

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

  GPIO.add_event_detect(T1, GPIO.BOTH, callback=btn_handler, bouncetime=100)
  GPIO.add_event_detect(T2, GPIO.BOTH, callback=btn_handler, bouncetime=100)

def cleanup():
  GPIO.cleanup()

def quit():
  pygame.quit()
  sys.exit()
  return

def btn_handler(channel):
  timer = Timeout()
  timer.cancel()
  display = pygame.display.get_surface()
  print("Button press detected: " + str(channel))
  # button press
  if not GPIO.input(channel):
    display.blit(img[channel], zero)
    pygame.display.update()
    timer.start()

def resetScreen():
  display = pygame.display.get_surface()
  display.blit(img['start'], zero)
  pygame.display.update()

# this line has to be below resetScreen
timer=threading.Timer(waitTime, resetScreen)
class Timeout(object):
  timer = None
  _instance = None

  def start(self):
    if self.timer != None:
      try:
        self.cancel()
      except:
        pass
    self.timer=threading.Timer(waitTime, resetScreen)
    self.timer.start()

  def cancel(self):
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


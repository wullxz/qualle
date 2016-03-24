#!/usr/bin/env python

from threading import Thread, Event, Timer, Lock
import time

def TimerReset(*args, **kwargs):
  """ Global function for Timer """
  return _TimerReset(*args, **kwargs)

class _TimerReset(Thread):
  """Call a function after a specified number of seconds:

  t = TimerReset(30.0, f, args=[], kwargs={})
  t.start()
  t.cancel() # stop the timer's action if it's still waiting
  """

  def __init__(self, interval, function, args=[], kwargs={}):
    Thread.__init__(self)
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.finished = Event()
    self.started = Event()
    self.done = Event()
    self.ignoreOnce = Event()
    self.ignoreOnce.clear()
    self.lock = Lock()

  def cancel(self):
    """ Stop the timer if it hasn't finished yet"""
    self.started.clear()
    self.finished.set()
    self.ignoreOnce.set()

  def run(self):
    while not self.done.isSet():
      self.ignoreOnce.clear()
      while self.started.isSet():
        self.lock.acquire()
        print("Start signal set!")
        print("Waiting for %d seconds..." % self.interval)
        self.finished.wait(self.interval)

        print("Done waiting!")

        if not self.finished.isSet() and not self.ignoreOnce.isSet():
          print("Calling function now!")
          self.function(*self.args, **self.kwargs)
        else:
          self.ignoreOnce.clear()
          print("Not running function because finished was set!")
        self.reset(self.interval)
        self.started.clear()
        self.lock.release()

  def restart(self):
    self.lock.acquire()
    self.finished.clear()
    self.started.set()
    self.lock.release()

  def reset(self, interval=None):
    """Reset the timer"""
    if interval:
      self.interval = interval

    self.started.clear()
    self.finished.set()

  def quit(self):
    """End and destroy this timer"""
    self.finished.set()
    self.done.set()

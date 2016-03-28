import ConfigParser
import sys

class Config(object):
  def __init__(self):
    self.raw = ConfigParser.ConfigParser()
    self.raw.read("/home/pi/Desktop/qualle/qualle.ini")
    mapsec = self.mapsection # shortcut to class method
    self.Pictures = mapsec("Pictures")
    self.QualleColors = mapsec("QualleColors")
    self.Taster = mapsec("Taster")
    self.TasterLED = mapsec("TasterLED")
    self.ColorLED = mapsec("ColorLED")
    self.General = mapsec("General")
    self.SPIChan1 = mapsec("SPIChan1")
    self.SPIChan2 = mapsec("SPIChan2")

  def mapsection(self, section):
    tmpdict = {}
    options = self.raw.options(section)
    for option in options:
      try:
        tmpdict[option] = self.raw.get(section, option)
        if tmpdict[option] == -1:
          DebugPrint("skip: %s" % option)
      except:
        print("exception on %s!" % option)
        print(sys.exc_info())
        tmpdict[option] = None
    return tmpdict

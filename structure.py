import configparser
from config import updateConfig
import json




class Entry:
    def __init__(self):
        pass
    def getKey(self):
        return self.key
    def getType(self):
        return self.type
    def getValue(self):
        return self.value
    def setKey(self, key):
        self.key = key
    def setType(self, type):
        self.type = type
    def setValue(self, value):
        self.value = value

def getEntry(entrylist, key):
    for e in entrylist:
        if e.getKey() == key:
            return e
    e = Entry()
    e.setKey(key)
    entrylist.append(e)
    return e 

def splitJson(entrylist, jsondata):
    for key in jsondata:
        e = getEntry(entrylist, key)
        if type(jsondata[key]) is list: 
            e.setType("a")
            e.setValue([])
            continue
        if type(jsondata[key]) is dict: 
            e.setType("d")
            e.setValue({})
            splitJson(e.getValue(), jsondata[key])
            continue
        # TODO enum
        e.setType("v")
        e.setValue("rnd")

def printStructure(entrylist, spacer = 0):
    for e in entrylist:
        print("{0}:{1}".format(e.getType(), e.getKey()))



updateConfig()
config = configparser.ConfigParser()
config.read('config.ini')

rootlist = []

with open(config["localnames"]["stations"], 'r') as f:
    for line in f:
        splitJson(rootlist, json.loads(line))

printStructure(rootlist)

import json
import random

def loadjson(filename):
    with open(filename) as jsonfile:
        jsondata = json.load(jsonfile)
        return jsondata

def getrandspawn(moninfo):
    correctmon = []
    for mon in moninfo:
        if not getflag(moninfo[mon].get('flags'), 'nospawn'):
            correctmon.append(mon)
    return correctmon[random.randint(0, len(correctmon)-1)]

def getrandflagged(moninfo, flagname):
    correctmon = []
    for mon in moninfo:
        if getflag(moninfo[mon].get('flags'), flagname):
            correctmon.append(mon)
    return correctmon[random.randint(0, len(correctmon)-1)]

def getflagged(moninfo, flagname):
    correctmon = []
    for mon in moninfo:
        if not getflag(moninfo[mon].get('flags'), flagname):
            correctmon.append(mon)
    return correctmon

def getflag(flags, flagsearch):
    if flags is not None:
        for flag in flags:
            if flag == flagsearch:
                return True
    return False
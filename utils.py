import random
import pygame.locals as pg


def getrandomdelta(max):
    if random.randint(0, 1) == 1:
        return random.randint(0, max)
    else:
        return -random.randint(0, max)


def getkey(keystroke):
    try:
        return getattr(pg, 'K_'+keystroke)
    except:
        return None


def populatekeys(keylist):
    truekeys = []
    for key in keylist:
        if getkey(key) is not None:
            truekeys.append(getkey(key))
    return truekeys


def loadtextfile(filename):
    lines = []
    try:
        f = open(filename, "r")
        for line in f:
            line = line.rstrip()
            lines.append(line)
        f.close()
        return lines
    except IOError:
        return lines

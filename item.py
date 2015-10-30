import gameEngine
import thing
import pathfinder
import random
import effect

class Item(thing.Thing):
    x = 0
    y = 0
    mapfield = None
    parameters = {}
    gameengine = None
    stack = 1

    def __init__(self, parameters, gameengine):
        self.delay = 0
        self.parameters = dict(parameters)
        self.gameengine = gameengine

    def setposition(self, coord):
        self.x = coord[0]
        self.y = coord[1]

    def getname(self):
        return self.parameters["id"]

    def getposition(self):
        return self.x, self.y

    def getvisualpos(self, tilesize):
        return self.x*tilesize, self.y*tilesize

    def setparam(self, param, newvalue):
        oldvalue = self.parameters[param]
        self.parameters[param] = newvalue
        self.gameengine.gameevent.report(self, param, newvalue, oldvalue)

    def getparam(self, name):
        try:
            return self.parameters[name]
        except KeyError:
            return None

    def getflag(self, flagname):
        flags = self.parameters.get('flags')
        if flags is not None:
            for flag in self.parameters.get('flags'):
                if flag == flagname:
                    return True
        return False

    def update(self):
        if (self.getflag("gravity") and self.delay == 1) or (self.getflag("gravity") and not self.getflag("delay")):
            if not self.gameengine.mapfield.isgrounded(self.getposition()):
                self.setposition((self.x, self.y + 1))
        # delay set for projectiles, not fall immidiately after firing
        if self.getflag("delay") and self.delay == 0:
            self.delay = 1
        if self.getparam("fuse") is not None:
            if int(self.getparam("fuse")) == 0:
                neweffect = effect.Effect(self.gameengine.effinfo[self.getparam("fuseeffect")], self.gameengine)
                neweffect.setposition(self.getposition())
                self.gameengine.mapfield.effects.append(neweffect)
                self.gameengine.mapfield.items.remove(self)
            elif int(self.getparam("fuse")) != -1:
                self.setparam("fuse", int(self.getparam("fuse")) - 1)

    def geteffect(self):
        if self.parameters['effect'] != "None":
            return self.parameters['effect']
        else:
            return None

    def getvalue(self):
        return self.parameters['value']

    def addtostack(self, item):
        self.stack += item.stack
        if self.gameengine.mapfield.items.__contains__(item):
            self.gameengine.mapfield.items.remove(item)

    def isstackable(self):
        if self.getparam("stackable") == "true":
            return True
        else:
            return False
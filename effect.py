import gameEngine
import thing
import pathfinder
import copy

class Effect(thing.Thing):
    x = 0
    y = 0
    parameters = {}
    gameengine = None
    ttl = 1
    donotupdate = False
    flags = []

    def __init__(self, parameters, gameengine):
        self.parameters = dict(parameters)
        self.gameengine = gameengine
        self.ttl = parameters['ttl']

    def setposition(self, coord):
        self.x = coord[0]
        self.y = coord[1]

    def getname(self):
        return self.parameters["id"]

    def getposition(self):
        return self.x, self.y

    def getvisualpos(self, tilesize):
        return self.x*tilesize, self.y*tilesize

    def geteffect(self):
        return self.parameters['effect']

    def getparam(self, name):
        try:
            return self.parameters[name]
        except KeyError:
            return None

    def setparam(self, param, newvalue):
        oldvalue = self.parameters[param]
        self.parameters[param] = newvalue
        #if self.gameengine.gameevent is not None:
            #self.gameengine.gameevent.debug(self, param, newvalue, oldvalue)

    def getflag(self, flagname):
        flags = self.parameters.get('flags')
        if flags is not None:
            for flag in self.parameters.get('flags'):
                if flag == flagname:
                    return True
        return False

    def update(self):
        if self.donotupdate is True:
            self.donotupdate = False
            self.ttl -= 1
            return False
        if self.getflag("random") and self.ttl > 1:
            randcoord = self.gameengine.mapfield.getrandomnearby(self.getposition())
            if randcoord is not None:
                self.setposition(randcoord)
        if self.getflag("disperse") and self.ttl > 1:
            dispcoord = self.gameengine.mapfield.getrandomnearby(self.getposition())
            if dispcoord is not None:
                neweffect = Effect(self.gameengine.effinfo[self.getname()], self.gameengine)
                neweffect.setposition(dispcoord)
                neweffect.ttl = self.ttl - 1
                neweffect.donotupdate = True
                self.gameengine.mapfield.effects.append(neweffect)
        if self.getflag("large") and self.ttl > 1:
            neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for n in neighbors:
                ncoord = pathfinder.alterposition(self.getposition(), n)
                neweffect = Effect(self.gameengine.effinfo[self.getname()], self.gameengine)
                neweffect.setposition(ncoord)
                neweffect.ttl = self.ttl
                # remove large to prevent flood
                # copy because we don't want to change the flags in global effects library
                flags = copy.copy(neweffect.getparam("flags"))
                for f in flags:
                    if f == "large":
                        flags.remove(f)
                        break
                neweffect.setparam("flags", flags)
                self.gameengine.mapfield.effects.append(neweffect)
        if self.getparam("damage") and self.ttl > 1:
            occupant = self.gameengine.mapfield.getoccupants(self.getposition())
            if occupant is not None:
                if not (occupant.getflag("relectric") and self.getflag("electric")):
                    occupant.lowerhealth(self.getparam("damage"))
        if self.getparam("effect") == "repair":
            occupant = self.gameengine.mapfield.getoccupants(self.getposition())
            if occupant is not None:
                occupant.raisehealth(int(self.getparam("amount")))

        self.ttl -= 1

    def getspawn(self):
        return self.getparam("spawn")
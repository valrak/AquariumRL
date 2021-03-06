import gameEngine
import thing
import item
import pathfinder
import copy

class Effect(thing.Thing):
    x = 0
    y = 0
    parameters = {}
    gameengine = None
    ttl = 1
    donotupdate = False
    owner = None
    updated = False
    flags = []

    def __init__(self, parameters, gameengine):
        self.parameters = dict(parameters)
        self.gameengine = gameengine
        self.ttl = parameters['ttl']
        if self.ttl == -1:
            self.ttl = None

    def resetupdate(self):
        self.updated = False

    def isupdated(self):
        return self.updated

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

    def getowner(self):
        return self.owner

    def setowner(self, owner):
        self.owner = owner

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

    def large(self):
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for n in neighbors:
            ncoord = pathfinder.alterposition(self.getposition(), n)
            protoeffect = copy.copy(self.gameengine.effinfo[self.getname()])
            # remove large to prevent flood
            # copy because we don't want to change the flags in global effects library
            flags = copy.copy(protoeffect["flags"])
            for f in flags:
                if f == "large":
                    flags.remove(f)
                    break
            protoeffect["flags"] = flags
            neweffect = Effect(protoeffect, self.gameengine)
            neweffect.setposition(ncoord)
            neweffect.setowner(self.owner)
            neweffect.ttl = self.ttl

            neweffect.setparam("flags", flags)
            self.gameengine.mapfield.effects.append(neweffect)
            neweffect.update()

    def update(self):
        self.updated = True
        if self.getflag("large"):
            self.large()
        if self.donotupdate is True:
            self.donotupdate = False
            if self.ttl is not None:
                self.ttl -= 1
            return False
        if self.ttl > 1 or self.ttl is None:
            if self.getflag("random"):
                randcoord = self.gameengine.mapfield.getrandomoccnearby(self.getposition())
                if randcoord is not None:
                    self.setposition(randcoord)
            if self.getflag("disperse"):
                dispcoord = self.gameengine.mapfield.getrandomnearby(self.getposition())
                if dispcoord is not None:
                    neweffect = Effect(self.gameengine.effinfo[self.getname()], self.gameengine)
                    neweffect.setposition(dispcoord)
                    neweffect.ttl = self.ttl - 1
                    neweffect.donotupdate = True
                    neweffect.setowner(self.owner)
                    self.gameengine.mapfield.effects.append(neweffect)
            if self.getparam("damage"):
                occupant = self.gameengine.mapfield.getoccupants(self.getposition())
                if occupant is not None:
                    if not (occupant.getflag("relectric") and self.getflag("electric")):
                        occupant.lowerhealth(self.getparam("damage"))
                        self.gameengine.gameevent.report(occupant.getname()+" has been hit by "+self.getname()+"!")
                        if self.owner is not None:
                            occupant.lastattacker = self.owner
            if self.getparam("effect") == "repair":
                occupant = self.gameengine.mapfield.getoccupants(self.getposition())
                if occupant is not None:
                    occupant.raisehealth(int(self.getparam("amount")))
            if self.getparam("effect") == "tele":
                occupant = self.gameengine.mapfield.getoccupants(self.getposition())
                if occupant is not None:
                    newlocation = self.gameengine.mapfield.getrandomsafe()
                    if newlocation is not None:
                        occupant.setposition(newlocation)
                        self.gameengine.gameevent.report(occupant.getname()+" teleported to another location!")
            if self.getparam("effect") == "gate":
                occupant = self.gameengine.mapfield.getoccupants(self.getposition())
                if occupant is not None and occupant.player:
                    occupant.setparam("level", int(occupant.getparam("level")) + 1)
                    self.gameengine.noscore = False
                    self.gameengine.graphicshandler.erasepops()
                    goldscore_add = occupant.goldscore()
                    self.gameengine.gameevent.report("Merfolk are ecstatic!")
                    if goldscore_add > 0:
                        self.gameengine.gameevent.report("You got "+str(goldscore_add)+" points for the gold items brought to gate.")
                    if int(occupant.getparam("level")) >= self.gameengine.LASTLEVEL:
                        occupant.win()
                        self.gameengine.state = "reset"
                    else:
                        self.gameengine.gameevent.report("Choose your reward!")
                        self.gameengine.newmap()
                        self.gameengine.itemsgenerated = 0
                        self.gameengine.mapfield.getplayer().killcount = 0
                        self.gameengine.state = "upgrade"
            if self.getparam("effect") == "give":
                amount = 1
                if self.getparam("amount") is not None:

                    amount = int(self.getparam("amount"))
                if self.getparam("itemname") is not None:
                    for i in range(amount):
                        self.gameengine.mapfield.addatrandomsurfaceitem(
                            item.Item(self.gameengine.iteinfo[self.getparam("itemname")], self.gameengine))
                    self.gameengine.gameevent.report(
                        str(self.getparam("amount")) + " of " + self.getparam("itemname") + " was thrown into the arena.")
            if self.getparam("effect") == "change":
                occupant = self.gameengine.mapfield.getoccupants(self.getposition())
                if occupant is not None:
                    if self.getparam("changeattributesname") is not None and self.getparam("changeattributesvalue") is not None:
                        i = 0
                        values = self.getparam("changeattributesvalue")
                        for attname in self.getparam("changeattributesname"):
                            paramvalue = int(occupant.getparam(attname))
                            occupant.setparam(attname, paramvalue + int(values[i]))
                            i += 1
        if self.ttl is not None:
            self.ttl -= 1

    def getspawn(self):
        return self.getparam("spawn")
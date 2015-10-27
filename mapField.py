import pathfinder
import random
from effect import *
from item import *
import csv

WALL = '0'
FREE = '1'
STAIRS = '2'

''' random things generator constants '''
GENERATOR_CHANSERISE = 20  # percentile of random chance rising after not generating anything
GENERATOR_TRESHOLD = 50
GENERATOR_OODUP = 10 # out of depth chance to spawn higher level thing
GENERATOR_OODDOWN = 30 # chance to spawn lower level thing


class MapField(object):
    gameengine = None
    terrain = None
    terinfo = None
    genmonsters = []
    genitems = []
    passablemap = None
    monsters = []
    items = []
    effects = []
    moninfo = None
    maxx = 0
    maxy = -1
    genlast = 0 # number of turns for which was not generated anything new

    def __init__(self, mapfile, mapinfo, moninfo, effinfo, iteinfo, gameengine):
        self.gameengine = gameengine
        self.terinfo = mapinfo
        self.moninfo = moninfo
        self.effinfo = effinfo
        self.iteinfo = iteinfo
        self.terrain = list(mapfile)
        for row in self.terrain:
            self.maxy += 1
        self.maxx = len(row)-1
        self.passablemap = self.generatepassablemap()

        # load database of level based creatures
        for dthing in self.moninfo:
            noadd = False
            cthing = self.moninfo[dthing]
            if "level" in cthing:
                if "flags" in cthing:
                    for flag in cthing["flags"]:
                        if flag == "nospawn":
                            noadd = True
                if not noadd:
                    self.genmonsters.append(cthing)
        for dthing in self.iteinfo:
            cthing = self.iteinfo[dthing]
            if "level" in cthing:
                self.genitems.append(cthing)

    def getplayer(self):
        for monster in self.monsters:
            if monster.player:
                return monster

    # basic pathfinding
    def findpath(self, start, end):
        return pathfinder.findpath(self.generatepassablemap(), start, end)

    # true if there is no visual/map obstruction in line
    def cansee(self, start, end):
        points = pathfinder.lineto(start, end)
        # if the distance is only one (original point and destination point), still can see
        if len(points) <= 2:
            return True
        for point in points:
            if not self.istransparent(point):
                return False
        return True

    # helper function for pathfinding algorithm
    def generatepassablemap(self):
        passmap = []
        y = 0
        for row in self.terrain:
            newrow = []
            for x in range(len(row)):
                if self.ispassable((x, y)):
                    newrow.append(pathfinder.Node(1, (x, y)))
                else:
                    newrow.append(pathfinder.Node(0, (x, y)))
            passmap.append(newrow)
            y += 1
        return passmap

    def getterrain(self, coord):
        if coord is not None:
            try:
                cell = self.terrain[coord[1]][coord[0]]
                return self.terinfo[cell]
            except IndexError, e:
                print "index error at coordinates:", coord, "Exception: ", e
                return None
        else:
            return None

    def ispassable(self, coord):
        if coord is not None and coord[0] < self.maxx and coord[1] < self.maxy and coord[0] >= 0 and coord[1] >= 0:
            cell = self.getterrain(coord)
            if (cell["passable"]) == "true" and self.getoccupants(coord) is None:
                return True
            else:
                return False
        return False

    def istransparent(self, coord):
        if coord is not None and coord[0] < self.maxx and coord[1] < self.maxy and coord[0] >= 0 and coord[1] >= 0:
            cell = self.getterrain(coord)
            if (cell["clear"]) == "true":
                effects = self.geteffects(cell)
                for effect in effects:
                    if effect.getparam("effect") == "novisibility":
                        return False
                return True
            else:
                return False
        return False

    def isfree(self, coord):
        if coord is not None and coord[0] < self.maxx and coord[1] < self.maxy and coord[0] >= 0 and coord[1] >= 0:
            cell = self.getterrain(coord)
            if (cell["passable"]) == "true" and self.getoccupants(coord) and self.geteffects(coord) is None:
                return True
            else:
                return False
        return False

    def getrandompassable(self):
        for i in range(100):
            coord = (random.randint(0, self.maxx), random.randint(0, self.maxy))
            if self.ispassable(coord):
                return coord
        # failed to obtain passable
        # TODO: obtain passable from nearest free cell at random location
        for y in range(self.maxy):
            for x in range(self.maxx):
                if self.ispassable((x, y)):
                    return coord
        return None

    def getrandomfree(self):
        for i in range(100):
            coord = (random.randint(0, self.maxx), random.randint(0, self.maxy))
            if self.isfree(coord):
                return coord
        # failed to obtain passable
        # TODO: obtain passable from nearest free cell at random location
        for y in range(self.maxy):
            for x in range(self.maxx):
                if self.isfree((x, y)):
                    return coord
        return None

    # returns random field in neigbors of given location
    def getrandomnearby(self, coord):
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        choose = []
        for n in neighbors:
            if self.ispassable((coord[0] + n[0], coord[1] + n[1])):
                choose.append(n)
        if len(choose) > 0:
            pos = choose[random.randint(0, len(choose)-1)]
            return coord[0] + pos[0], coord[1] + pos[1]
        return None

    def isclinged(self, coord, oldcoord=None):
        neighborcling = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for n in neighborcling:
            tempcoord = (coord[0] + n[0], coord[1] + n[1])
            if not oldcoord == tempcoord:
                occupant = self.getoccupants(tempcoord)
                if occupant is None or occupant.getflag("nomove"):
                    if not self.ispassable(tempcoord) and \
                        not self.getterrain(tempcoord)["id"] == "sky":
                        return True
        return False

    def isgrounded(self, coord):
        tempcoord = (coord[0], coord[1] + 1)
        occupant = self.getoccupants(tempcoord)
        if occupant is None or occupant.getflag("nomove"):
            if not self.ispassable(tempcoord):
                return True
        return False

    def getpassableground(self, coord, dirc):
        neighborsr = [(1, -1), (1, 1), (1, 0)]
        neighborsl = [(-1, -1), (-1, 1), (-1, 0)]

        if dirc == 1:
            neighbors = neighborsr
        else:
            neighbors = neighborsl
        for n in neighbors:
            newcoord = (coord[0] + n[0], coord[1] + n[1])
            if self.ispassable(newcoord) and self.isgrounded(newcoord):
                return newcoord
        return None

    def getpassablecling(self, coord, dirc):
        # neighborsr = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
        neighborsr = [(1, -1), (1, 1), (1, 0)]

        # neighborsl = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]
        neighborsl = [(-1, -1), (-1, 1), (-1, 0)]

        if dirc == 1:
            neighbors = neighborsr
        else:
            neighbors = neighborsl
        for n in neighbors:
            newcoord = (coord[0] + n[0], coord[1] + n[1])
            if self.ispassable(newcoord) and self.isclinged(newcoord, coord):
                return newcoord
        return None

    def getrandomground(self):
        choosefrom = []
        for y in range(self.maxy):
            for x in range(self.maxx):
                if self.ispassable((x, y)) and self.getterrain((x, y + 1))["passable"] == "false":
                    if self.ispassable((x + 1, y)) and self.ispassable((x - 1, y)):
                        choosefrom.append((x, y))
        if len(choosefrom) > 0:
            return choosefrom[random.randint(0, len(choosefrom)-1)]

    def getrandomsurface(self):
        choosefrom = []
        y = 0
        for x in range(self.maxx):
            if self.ispassable((x, y + 1)):
                choosefrom.append((x, y))
        if len(choosefrom) > 0:
            return choosefrom[random.randint(0, len(choosefrom)-1)]

    def getoccupants(self, coord):
        for monster in self.monsters:
            if (monster.x, monster.y) == coord:
                return monster
        return None

    def geteffects(self, coord):
        effects = []
        for effect in self.effects:
            if (effect.x, effect.y) == coord:
                effects.append(effect)
        return effects

    def getitems(self, coord):
        items = []
        for item in self.items:
            if (item.x, item.y) == coord:
                items.append(item)
        return items

    def addmonster(self, monster):
        self.monsters.append(monster)

    def addmonsterat(self, monster, coord):
        if self.getoccupants(coord) is None:
            monster.setposition(coord)
        else:
            monster.setposition(self.getrandomnearby(coord))
        if coord is not None:
            self.monsters.append(monster)

    def addrandomspawn(self):
        coord = self.getrandompassable()
        if coord is not None:
            neweffect = Effect(self.effinfo['spawn'], gameEngine)
            neweffect.setposition(coord)
            self.effects.append(neweffect)
        return coord

    def countmonsters(self, monstername):
        count = 0
        for monster in self.monsters:
            if monster.getname() == monstername:
                count += 1
        return count

    def addspawn(self, monstername):
        isgroundmon = False
        cthing = self.moninfo[monstername]
        if "limit" in cthing:  # Check if spawn number is not exceeded
            if int(cthing["limit"]) <= self.countmonsters(monstername):
                return None
        if "flags" in cthing:
            for flag in cthing["flags"]:
                if flag == "ground":  # Ground monsters
                    isgroundmon = True
                    break
        if isgroundmon:
            coord = self.getrandomground()
        else:
            coord = self.getrandompassable()
        if coord is not None:
            neweffect = Effect(self.effinfo['spawn'], gameEngine)
            neweffect.setposition(coord)
            neweffect.setparam("spawn", monstername)
            self.effects.append(neweffect)
        return coord

    # adds random monster and returns its coordinates
    def addatrandommonster(self, monster):
        if monster.getflag("ground"):
            coord = self.getrandomground()
        else:
            coord = self.getrandompassable()
        if coord is not None:
            monster.setposition(coord)
            self.monsters.append(monster)
        return coord

    # adds specific item on random surface coordinates
    def addatrandomsurfaceitem(self, item):
        coord = self.getrandomsurface()
        item.setposition(coord)
        self.items.append(item)

    # adds random level based item at random surface coordinates
    def addrandomsurfaceitem(self, level):
        lvlitems = []
        coord = self.getrandomsurface()
        for item in self.genitems:
            if level >= int(item["level"]):
                lvlitems.append(item)
        if len(lvlitems) > 0:
            ritem = random.randint(0, len(lvlitems)-1)
            gitem = Item(lvlitems[ritem], self.gameengine)
            gitem.setposition(coord)
            self.items.append(gitem)

    def generatemonster(self):
        self.genlast += 1
        chance = random.randint(0, GENERATOR_CHANSERISE * self.genlast)
        playerlvl = int(self.getplayer().getparam("level"))
        # generate random out of depth thing
        if chance > GENERATOR_TRESHOLD + GENERATOR_OODUP:
            self.addspawn(self.getmonsteratlevel(playerlvl+1))
            self.genlast = 0
        # generate normal depth thing
        elif chance > GENERATOR_TRESHOLD:
            self.addspawn(self.getmonsteratlevel(playerlvl))
            self.genlast = 0
        # generate lower depth thing
        elif chance > GENERATOR_TRESHOLD - GENERATOR_OODDOWN:
            if playerlvl != 1:
                playerlvl -= 1
            self.addspawn(self.getmonsteratlevel(playerlvl))
            self.genlast = 0

    def generateitem(self):
        self.genlast += 1
        chance = random.randint(0, GENERATOR_CHANSERISE * self.genlast)
        playerlvl = int(self.getplayer().getparam("level"))
        # generate random out of depth thing
        if chance > GENERATOR_TRESHOLD + GENERATOR_OODUP:
            self.addrandomsurfaceitem(playerlvl+1)
            self.genlast = 0
        # generate normal depth thing
        elif chance > GENERATOR_TRESHOLD:
            self.addrandomsurfaceitem(playerlvl)
            self.genlast = 0
        # generate lower depth thing
        elif chance > GENERATOR_TRESHOLD - GENERATOR_OODDOWN:
            if playerlvl != 1:
                playerlvl -= 1
            self.addrandomsurfaceitem(playerlvl)
            self.genlast = 0

    def getmonsteratlevel(self, level):
        lvlmonsters = []
        for mon in self.genmonsters:
            if level >= int(mon["level"]):
                lvlmonsters.append(mon)
        moni = random.randint(0, len(lvlmonsters)-1)
        return lvlmonsters[moni]["id"]

    # after each turn, clean the mess
    def cleanup(self):
        # remove monsters with hp less than 0
        found = []
        for monster in self.monsters:
            if monster.getparam("hp") <= 0:
                found.append(monster)
        for fdel in found:
            fdel.destroy()
            self.monsters.remove(fdel)

        # remove effects with overdo ttl
        found = []
        for effect in self.effects:
            if effect.ttl <= 0:
                found.append(effect)
        for fdel in found:
            self.effects.remove(fdel)
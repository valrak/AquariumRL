import pathfinder
import random
from effect import *
from item import *
import csv
import utils
import operator

''' random things generator constants '''
GENERATOR_CHANCERISEITEM = 20  # percentile of random chance rising after not generating anything
GENERATOR_CHANCERISEMONSTER = 16
GENERATOR_TRESHOLD = 50
GENERATOR_OODUP = 10  # out of depth chance to spawn higher level thing
GENERATOR_OODDOWN = 30  # chance to spawn lower level thing
COMBO_MULTIPLIER = 3 # how big combo bonus is during generating OOP items
NEIGHBORS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
SEQLOOKNEIGHBORS = [(-1, 0), (0, -1), (1, -1), (-1, -1)]

MAXROCKAMOUNT = 30
MINROCKAMOUNT = 80

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
    genlastmonster = 0 # for monsters

    def __del__(self):
        del self.monsters[:]
        del self.items[:]
        del self.gameengine
        del self.terrain[:]
        del self.effects[:]

    def __init__(self, mapfile, mapinfo, moninfo, effinfo, iteinfo, gameengine):
        self.gameengine = gameengine
        self.terinfo = mapinfo
        self.moninfo = moninfo
        self.effinfo = effinfo
        self.iteinfo = iteinfo

        if mapfile is not None:
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

    def generatelevel(self, maxx, maxy):
        self.maxx = maxx
        self.maxy = maxy
        self.terrain = []
        rockamountr = random.randint(MAXROCKAMOUNT, MINROCKAMOUNT)
        rockamount = maxx * maxy / rockamountr
        rockamountrand = maxx*maxy/95
        rocksize = 7
        rocksizerand = 5

        coralamount = maxx*maxy/60
        coralamountrand = maxx*maxy/70
        coralsize = 1
        coralsizerand = 3

        level = []
        for y in range(0, maxy):
            row = []
            if y == 0:
                for x in range(0, maxx):
                    row.append(",")
            elif y == maxy-1:
                for x in range(0, maxx):
                    row.append("#")
            else:
                for x in range(0, maxx):
                    if x == 0 or x == maxx-1:
                        row.append('0')
                    else:
                        row.append('.')
            self.terrain.append(row)
        for rock in range(0, rockamount + random.randint(0, rockamountrand)):
            x = random.randint(0, maxx-1)
            y = random.randint(0, maxy-1)
            if self.terrain[y][x] == '.':
                self.terrain[y][x] = '#'
            for fuzz in range(0, rocksize + random.randint(0, rocksizerand)):
                x += utils.getrandomdelta(1)
                y += utils.getrandomdelta(1)
                if y >= maxy:
                    y -= 1
                if x >= maxx:
                    x -= 1
                if y <= 0:
                    y += 1
                if x <= 0:
                    x += 1
                if self.terrain[y][x] == '.':
                    self.terrain[y][x] = '#'

        # corals
        coord = None
        for coral in range(0, coralamount + random.randint(0, coralamountrand)):
            if coord is None or random.randint(0, 1) == 1:
                coord = self.getrandomground()
            else:
                if self.isgrounded((coord[0]+1, coord[1])):
                    coord = (coord[0]+1, coord[1])
                elif self.isgrounded((coord[0]-1, coord[1])):
                    coord = (coord[0]-1, coord[1])
                else:
                    coord = self.getrandomground()
            # coord = self.getrandomground()
            coralgrowth = coralsize + random.randint(0, coralsizerand)
            for grow in range(0, coralgrowth):
                if self.ispassable(coord):
                    if self.terrain[coord[1]][coord[0]] == "%":
                        continue
                    if grow == 0 and self.ispassable((coord[0], coord[1]-1)) and coralgrowth > 1:
                        self.terrain[coord[1]][coord[0]] = "%"
                    elif grow == coralgrowth-1 or not self.ispassable((coord[0], coord[1]-1)):
                        self.terrain[coord[1]][coord[0]] = "^"
                        break
                    else:
                        self.terrain[coord[1]][coord[0]] = "|"
                coord = (coord[0], coord[1]-1)
        self.passablemap = self.generatepassablemap()
        self.removeisolatedplaces()
        self.passablemap = self.generatepassablemap()

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

    def isnonsolid(self, coord):
        if coord is not None and coord[0] < self.maxx and coord[1] < self.maxy and coord[0] >= 0 and coord[1] >= 0:
            cell = self.getterrain(coord)
            if (cell["passable"]) == "true":
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
            if (cell["passable"]) == "true" and self.getoccupants(coord) is None and len(self.geteffects(coord)) == 0:
                return True
            else:
                return False
        return False

    def getrandompassable(self, notnearplayer=False):
        listfree = []
        for y in range(self.maxy):
            for x in range(self.maxx):
                if self.ispassable((x, y)):
                    if notnearplayer and self.getplayer() is not None:
                        if not pathfinder.isnear((x, y), self.getplayer().getposition()):
                            listfree.append((x, y))
                    else:
                        listfree.append((x, y))

        if len(listfree) != 0:
            return listfree[random.randint(0, len(listfree) - 1)]
        else:
            for y in range(self.maxy):
                for x in range(self.maxx):
                    if self.ispassable((x, y)):
                        return x, y
        return None

        #
        # for i in range(100):
        #     coord = (random.randint(0, self.maxx), random.randint(0, self.maxy))
        #     if self.ispassable(coord):
        #         if notnearplayer and self.getplayer() is not None:
        #             if not pathfinder.isnear(coord, self.getplayer().getposition()):
        #                 return coord
        #         else:
        #             return coord
        # # failed to obtain passable
        # for y in range(self.maxy):
        #     for x in range(self.maxx):
        #         if self.ispassable((x, y)):
        #             return coord
        # return None

    def getrandomfree(self):
        listfree = []
        for y in range(self.maxy):
            for x in range(self.maxx):
                if self.isfree((x, y)):
                    listfree.append((x, y))
        if len(listfree) != 0:
            return listfree[random.randint(0, len(listfree)-1)]
        return None

    def issafe(self, coord):
        if coord is not None and coord[0] < self.maxx and coord[1] < self.maxy and coord[0] >= 0 and coord[1] >= 0:
            cell = self.getterrain(coord)
            if (cell["passable"]) == "true" and self.getoccupants(coord) is None and len(self.geteffects(coord)) == 0:
                neighbors = self.getneighbors(coord[0], coord[1])
                for n in neighbors:
                    if self.getoccupants(n) is not None:
                        return False
                return True
            else:
                return False
        return False

    def getrandomsafe(self):
        listsafe = []
        for y in range(self.maxy):
            for x in range(self.maxx):
                if self.issafe((x, y)):
                    listsafe.append((x, y))
        if len(listsafe) != 0:
            return listsafe[random.randint(0, len(listsafe)-1)]
        else:
            return self.getrandomfree()
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

    # returns random field in neigbors of given location without considering occupants
    def getrandomoccnearby(self, coord):
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        choose = []
        for n in neighbors:
            if self.isnonsolid((coord[0] + n[0], coord[1] + n[1])):
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
                    if not self.ispassable(tempcoord) and not self.getterrain(tempcoord)["id"] == "sky":
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
                    if self.ispassable((x + 1, y)) and self.ispassable((x - 1, y)) and self.isgrounded((x, y)):
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
        coord = self.getrandompassable(True)
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
            coord = self.getrandompassable(True)
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
            coord = self.getrandompassable(True)
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
            # rarity
            raritems = []
            for item in lvlitems:
                if item.has_key("rarity") and item["rarity"]:
                    rarity = random.randint(1, 10)
                    if int(item["rarity"]) <= rarity:
                        raritems.append(item)
                else:
                    raritems.append(item)

            if len(raritems) >= 1:
                if len(raritems) == 1:
                    ritem = 0
                else:
                    ritem = random.randint(0, len(raritems)-1)
                gitem = Item(raritems[ritem], self.gameengine)
                gitem.setposition(coord)
                self.items.append(gitem)

    def generatemonster(self):
        if self.gameengine.state == "reset":
            return
        self.genlastmonster += 1
        chance = random.randint(0, GENERATOR_CHANCERISEMONSTER * self.genlastmonster)
        playerlvl = int(self.getplayer().getparam("level"))
        # generate random out of depth thing
        if chance > GENERATOR_TRESHOLD + GENERATOR_OODUP:
            self.addspawn(self.getmonsteratlevel(playerlvl+1))
            self.genlastmonster = 0
        # generate normal depth thing
        elif chance > GENERATOR_TRESHOLD:
            self.addspawn(self.getmonsteratlevel(playerlvl))
            self.genlastmonster = 0
        # generate lower depth thing
        elif chance > GENERATOR_TRESHOLD - GENERATOR_OODDOWN:
            if playerlvl != 1:
                playerlvl -= 1
            self.addspawn(self.getmonsteratlevel(playerlvl))
            self.genlastmonster = 0

    def generateitem(self, now=False):
        if self.gameengine.state == "reset":
            return
        if now:
            chance = 50 + self.getplayer().combo * COMBO_MULTIPLIER
        else:
            self.genlast += 1
            chance = random.randint(0, GENERATOR_CHANCERISEITEM * self.genlast)
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

    def generategate(self):
        neweffect = effect.Effect(self.gameengine.effinfo["gate"], self.gameengine)
        neweffect.setposition(self.getrandompassable())
        self.gameengine.mapfield.effects.append(neweffect)

    def gategenerated(self):
        for eff in self.effects:
            if eff.getid() == "gate":
                return True
        return False

    def getmonsteratlevel(self, level):
        lvlmonsters = []
        for mon in self.genmonsters:
            if level >= int(mon["level"]):
                lvlmonsters.append(mon)
        if len(lvlmonsters) > 0:
            # rarity
            rarmons = []
            for mon in lvlmonsters:
                if mon["rarity"]:
                    rarity = random.randint(1, 10)
                    if int(mon["rarity"]) <= rarity:
                        rarmons.append(mon)
                else:
                    rarmons.append(mon)

            if len(rarmons) >= 1:
                if len(rarmons) == 1:
                    moni = 0
                else:
                    moni = random.randint(0, len(rarmons)-1)
                return lvlmonsters[moni]["id"]
        return None

    # after each turn, clean the mess
    def cleanup(self):
        # remove monsters with hp less than 0
        found = []
        for monster in self.monsters:
            if monster.getparam("hp") <= 0:
                found.append(monster)
        for fdel in found:
            if fdel in self.monsters:
                self.monsters.remove(fdel)
            fdel.destroy()

        # remove effects with overdo ttl
        found = []
        for effect in self.effects:
            if effect.ttl is not None and effect.ttl <= 0:
                found.append(effect)
        for fdel in found:
            if fdel in self.effects:
                self.effects.remove(fdel)

    def replacemap(self):
        player = self.getplayer()
        del self.effects[:]
        del self.items[:]
        del self.monsters[:]
        del self.terrain[:]
        self.generatelevel(self.maxx, self.maxy)
        player.setposition(self.getrandomfree())
        self.monsters.append(player)

    def getneighbors(self, x, y, neighlist=NEIGHBORS):
        neigh = []
        for n in neighlist:
            if (((x + n[0]) > self.maxx) or ((x + n[0]) < 0) or
                    ((y + n[1]) > self.maxy) or ((y + n[1]) < 0)):
                neigh.append(None)
            else:
                neigh.append((x + n[0], y + n[1]))
        return neigh

    def removeisolatedplaces(self):
        def replaceregion(fromvalue, tovalue):
            x = 0
            y = 0
            for row in regionvaluemap:
                for column in row:
                    if regionvaluemap[y][x] == fromvalue:
                        regionvaluemap[y][x] = tovalue
                    x += 1
                x = 0
                y += 1
            # remove also from region number list
            if fromvalue in regionnumbers:
                lastamount = regionnumbers.get(fromvalue)
                regionnumbers.pop(fromvalue)
            else:
                lastamount = 1
            updateamount = regionnumbers.get(tovalue)
            regionnumbers.update({tovalue: updateamount + lastamount})

        # Create a region counter
        regionvaluemap = []
        for y in range(self.maxy + 1):
            row = []
            for x in range(self.maxx + 1):
                row.append(0)
            regionvaluemap.append(row)

        maxregion = 1
        regionnumbers = {}
        y = 0
        x = 0
        for row in self.terrain:
            for column in row:
                if self.ispassable((x, y)):
                    region = maxregion
                    newregion = True
                    # check the northeast, north, northwest, and west pixel are connected
                    neighbors = self.getneighbors(x, y, SEQLOOKNEIGHBORS)
                    for n in neighbors:
                        if n is not None:
                            neighbourvalue = regionvaluemap[n[1]][n[0]]
                            # check if it is traversable
                            if neighbourvalue > 0:
                                if region < neighbourvalue:
                                    # found region which is actually connected to this
                                    replaceregion(neighbourvalue, region)
                                    newregion = False
                                # need to correct current region as we've found another one
                                elif neighbourvalue < region:
                                    replaceregion(region, neighbourvalue)
                                    newregion = False
                                    region = neighbourvalue
                                else:
                                    # found connected to current already
                                    if not region == neighbourvalue:
                                        region = neighbourvalue
                                        regionnumbers.update({region: int(regionnumbers.get(region) + 1)})
                                    newregion = False
                    regionvaluemap[y][x] = region
                    # new region, assign new number
                    if newregion:
                        maxregion += 1
                        regionnumbers.update({region: 1})
                x += 1
            y += 1
            x = 0

        # fill the isolated tiles
        regions = sorted(regionnumbers.items(), key=operator.itemgetter(1), reverse=True)
        y = 0
        x = 0
        for row in self.terrain:
            for column in row:
                if regionvaluemap[y][x] != 0 and regionvaluemap[y][x] != regions[0][0]:
                    self.terrain[y][x] = "#"
                x += 1
            y += 1
            x = 0
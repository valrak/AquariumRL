import gameEngine
import thing
import pathfinder
import random
import item
import effect

class Monster(thing.Thing):
    x = 0
    y = 0
    player = False
    rangedpreference = None
    mapfield = None
    parameters = {}
    gameengine = None
    lastseen = None
    respawntime = 0  # used for spawners only
    firetime = 0  # used for ranged combatants
    home = None
    children = None
    direction = None
    inventory = None
    lastattacker = None
    maxhp = 0
    score = 0

    def __init__(self, parameters, gameengine):
        self.parameters = dict(parameters)
        self.gameengine = gameengine
        self.children = []
        self.inventory = []
        if self.getparam("hp") is not None:
            self.maxhp = int(self.getparam("hp"))
        if self.getparam("firelimit") is not None:
            self.firetime = int(self.getparam("firelimit"))

    def setposition(self, coord):
        self.x = coord[0]
        self.y = coord[1]

    def getname(self):
        return self.parameters["id"]

    def getposition(self):
        return self.x, self.y

    def getvisualpos(self, tilesize):
        return self.x*tilesize, self.y*tilesize

    def action(self, coord):
        mapfield = self.gameengine.mapfield
        # determine what to do with occupant of the field
        if mapfield.getoccupants(coord) is not None:
            occupant = mapfield.getoccupants(coord)
            occupant.combat(self)

        # move to free field if not obstructed
        if mapfield.ispassable(coord):
            self.setposition(coord)

    def setparam(self, param, newvalue):
        oldvalue = self.parameters[param]
        self.parameters[param] = newvalue
        self.gameengine.gameevent.report(self, param, newvalue, oldvalue)

    def lowerhealth(self, amount):
        self.setparam("hp", int(self.getparam("hp")) - int(amount))

    def raisehealth(self, amount):
        if (int(self.getparam("hp")) + amount) > self.maxhp:
            newhp = self.maxhp
        else:
            newhp = int(self.getparam("hp")) + amount
        self.setparam("hp", newhp)

    def combat(self, attacker):
        self.lastattacker = attacker
        self.setparam("hp", int(self.getparam("hp")) - int(attacker.getparam("attack")))

    def rangedcombat(self, weapon, attacker):
        if int(weapon.getparam("damage") > 0):
            self.lastattacker = attacker
        effects = self.gameengine.mapfield.geteffects(self.getposition())
        for eff in effects:
            if eff.getflag("novisibility"):
                return False
        self.setparam("hp", int(self.getparam("hp")) - int(weapon.getparam("damage")))

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
        # update level
        if self.player:
            scorelevel = 1
            for nextscore in self.gameengine.SCORETABLE:
                scorelevel += 1
                level = int(self.getparam("level"))
                if level < scorelevel:
                    if nextscore <= self.score:
                        self.setparam("level", level + 1)
                        #self.gameengine.gameevent.report("Diver raised his level to "+str(self.getparam("level"))+"!", None, None, None)
        # weight management
        if self.getparam("weightLimit") is not None:
            totalw = 0
            for witem in self.inventory:
                if witem.getparam("weight") is not None:
                    totalw += int(witem.getparam("weight"))
            if totalw > int(self.getparam("weightLimit")):

                coord = (self.x, self.y+1)
                if self.gameengine.mapfield.ispassable(coord):
                    self.setposition(coord)
        # ai
        if not self.player:
            # not applicable for player
            actions = 0
            while self.canact(actions):
                # I like to collect various things, if there are any under me, take them!
                playerpos = self.gameengine.mapfield.getplayer().getposition()
                position = self.getposition()
                if self.getflag("collector"):
                    # if I am near home, I'll put there my items
                    if self.home is not None and len(self.inventory) > 0:
                        if pathfinder.isnear(self.home.getposition(), self.getposition()):
                            self.giveall(self.home)
                            actions += 1
                    localitems = self.gameengine.mapfield.getitems(self.getposition())
                    if len(localitems) > 0:
                        for witem in localitems:
                            self.pick(witem)
                        actions += 1
                # I shoot random things
                if self.getflag("randomshot") and self.gameengine.mapfield.cansee(position, playerpos) and self.canact(actions):
                    bestranged = self.getbestranged()
                    if bestranged is not None and self.firetime == 0:
                        vector = self.gameengine.mapfield.getrandomnearby(self.getposition())
                        vector = (vector[0] - self.getposition()[0], vector[1])
                        vector = (vector[0], vector[1] - self.getposition()[1])
                        self.fire(vector, bestranged)
                        actions += 1
                        if self.getparam("firelimit") is not None:
                            self.firetime = int(self.getparam("firelimit"))

                # I have ranged capability and see the target
                if self.getflag("ranged") and self.gameengine.mapfield.cansee(position, playerpos) and self.canact(actions):
                    bestranged = self.getbestranged()
                    if bestranged is not None and self.firetime == 0:
                        # if the player is near me and I have better attack than ranged weapon, then bash him
                        if pathfinder.isnear(playerpos, position) and int(bestranged.getparam("damage")) < int(self.getparam("attack")):
                            False
                        # if is in range an line, shoot!
                        else:
                            direct = pathfinder.finddirection(position, playerpos)
                            if direct is not None:
                                wrange = int(bestranged.getparam("range"))
                                linetotarget = pathfinder.lineto(position, playerpos)
                                linetotarget = linetotarget[1:-1]
                                if len(linetotarget) <= wrange:
                                    # check if there is anything in the path
                                    canshoot = True
                                    for p in linetotarget:
                                        if not self.gameengine.mapfield.ispassable(p):
                                            canshoot = False
                                    if canshoot:
                                        self.fire(direct, bestranged)
                                        actions += 1
                                        if self.getparam("firelimit") is not None:
                                            self.firetime = int(self.getparam("firelimit"))

                # if can move then move to player
                if not self.getflag("nomove") and not self.getflag("ground") and self.canact(actions):
                    if not self.player:
                        if self.lastseen == position:
                            self.lastseen = None
                        if self.gameengine.mapfield.cansee(position, playerpos):
                            # I will remember where I've seen target
                            self.lastseen = playerpos
                            goto = self.gameengine.mapfield.findpath(position, playerpos)
                            if goto is not None:
                                self.action(goto)
                            else:  # wander randomly
                                self.action(self.gameengine.mapfield.getrandomnearby(position))
                        # if I can't see player, I will go to place where I've last seen target
                        elif self.lastseen is not None:
                            goto = self.gameengine.mapfield.findpath(position, self.lastseen)
                            if goto is not None:
                                self.action(goto)
                            # can't see target even here, where I've last seen him
                        else: # wander randomly
                            self.action(self.gameengine.mapfield.getrandomnearby(position))
                    actions += 1

                # can move only on ground
                if self.getflag("ground") and not self.getflag("nomove") and self.canact(actions):
                    playerpos = self.gameengine.mapfield.getplayer().getposition()
                    position = self.getposition()
                    if not self.player:
                        # if the player is nearby, I will cut him
                        if len(pathfinder.lineto(position, playerpos)) == 2:
                            self.action(playerpos)
                        # I don't have anything to hold to, I will fall
                        if not self.gameengine.mapfield.isgrounded(self.getposition()):
                            self.action((self.x, self.y + 1))
                        # or i will wander by one direction
                        else:
                            if self.direction is None:
                                directions = [-1, 1]
                                self.direction = directions[random.randint(0, 1)]
                            goto = self.gameengine.mapfield.getpassableground(self.getposition(), self.direction)
                            if goto is None:
                                self.direction *= -1
                            self.action(goto)
                # check isgrounded, if not fall down
                if self.getflag("ground") and not self.gameengine.mapfield.isgrounded(self.getposition()):
                    coord = (self.x, self.y+1)
                    if self.gameengine.mapfield.ispassable(coord):
                        self.setposition(coord)

                actions += 1
        # manage spawners, applicable for player
        if self.getparam("firelimit") is not None:
            if self.firetime > 0:
                self.firetime -= 1
        if self.getflag("spawner"):
            # spawn children if there are less than should be
            if len(self.children) < int(self.getparam("spawnlimit")):
                self.respawntime += 1
                if self.respawntime >= int(self.getparam("respawntime")):
                    #spawnpos = self.gameengine.mapfield.getrandomnearby(self.getposition())
                    #if spawnpos is not None:
                    #todo: spawn position should be besides, but should not move yet
                    child = Monster(self.gameengine.moninfo[self.getparam("spawn")], self.gameengine)
                    child.home = self
                    #child.setposition(spawnpos)
                    child.setposition(self.getposition())
                    self.children.append(child)
                    self.gameengine.mapfield.addmonster(child)
                    self.respawntime = 0

    def destroy(self):
        # draw blood
        neweffect = effect.Effect(self.gameengine.effinfo["blood"], self.gameengine)
        neweffect.setposition(self.getposition())
        self.gameengine.mapfield.effects.append(neweffect)
        # drop all items
        self.dropall()
        # inform home that I'm not going home any more
        if self.home is not None:
            self.home.removechild(self)
        # inform children that their home is destroyed
        for child in self.children:
            if not child.isalive:
                self.child.home = None
        # increase score for the attacker
        if self.lastattacker is not None and self.getparam("score") is not None and not self.gameengine.noscore:
            self.lastattacker.score += int(self.getparam("score"))
            # fixme: include score when killed with item (dynamite). Item should have lastused.
            self.gameengine.gameevent.report(self.getname()+" killed by "+self.lastattacker.getname()+"!", None, None, None)
        else:
            self.gameengine.gameevent.report(self.getname()+" has been killed! ", None, None, None)
        # game reset
        if self.player:
            self.gameengine.resetflag = True

    def removechild(self, child):
        self.children.remove(child)

    def isalive(self):
        if self.getparam("hp") <= 0:
            return False
        return True

    def pick(self, ite):
        if self.getitem(ite.getname()) is not None and ite.isstackable():
            self.getitem(ite.getname()).addtostack(ite)
        else:
            self.inventory.append(ite)
            if self.gameengine.mapfield.items.__contains__(ite):
                self.gameengine.mapfield.items.remove(ite)
                if ite.getparam("fuse") is not None:
                    ite.setparam("fuse", -1)

    def fire(self, direction, what=None):
        weapon = what
        if what is None:
            if self.rangedpreference is None:
                weapon = self.getbestranged()
            else:
                weapon = self.rangedpreference
        if weapon is None:
            return None
        weapon.setposition(self.getposition())
        weapon = self.throwaway(weapon)
        # set fuse for fused weapons
        if weapon.getparam("defaultFuse") is not None and weapon.getparam("fuse") is not None:
            weapon.setparam("fuse", int(weapon.getparam("defaultFuse")))
        self.gameengine.mapfield.items.append(weapon)
        if weapon.getparam("range") is not None:
            wrange = weapon.getparam("range")
        else:  # weapon not meant as ranged
            wrange = 0
        for i in range(0, wrange):
            newposition = pathfinder.alterposition(weapon.getposition(), direction)
            monsterat = self.gameengine.mapfield.getoccupants(newposition)
            # if weapon hits any monster
            if monsterat is not None:
                monsterat.rangedcombat(weapon, self)
                break
            # if weapon hits obstacle
            elif not self.gameengine.mapfield.ispassable(newposition):
                break
            # if not, it flies to its range
            else:
                weapon.setposition(newposition)
                if weapon.geteffect() is not None:
                    neweffect = effect.Effect(self.gameengine.effinfo[weapon.geteffect()], self.gameengine)
                    neweffect.setposition(weapon.getposition())
                    self.gameengine.mapfield.effects.append(neweffect)
            #self.gameengine.gameevent.report("fire", )
        if weapon.getflag("nodrop"):
            self.gameengine.mapfield.items.remove(weapon)

    def useitem(self, ite):
        if ite.getflag("usable") and ite.geteffect() is not None:
            neweffect = effect.Effect(self.gameengine.effinfo[ite.geteffect()], self.gameengine)
            neweffect.setposition(self.getposition())
            self.gameengine.mapfield.effects.append(neweffect)
            if ite.isstackable() and ite.stack > 1:
                ite.stack -= 1
            else:
                self.inventory.remove(ite)

    def getinventory(self, flag):
        if flag is None:
            return self.inventory
        else:
            itemlist = []
            for ite in self.inventory:
                if ite.getflag(flag):
                    itemlist.append(ite)
            return itemlist

    def drop(self, ite):
        ite.setposition(self.getposition())
        self.inventory.remove(ite)
        self.gameengine.mapfield.items.append(ite)

    def throwaway(self, ite):
        if self.inventory.__contains__(ite):
            if ite.isstackable:
                if ite.stack > 1:
                    ite.stack -= 1
                else:
                    self.inventory.remove(ite)
                    self.rangedpreference = None
                pos = ite.getposition()
                ite = item.Item(self.gameengine.iteinfo[ite.getname()], self.gameengine)
                ite.setposition(pos)
            else:
                self.inventory.remove(ite)
        return ite

    def dropall(self):
        todrop = []
        for ite in self.inventory:
            todrop.append(ite)
        for ite in todrop:
            self.drop(ite)

    # inventory methods
    def getitem(self, itemname):
        for ite in self.inventory:
            if ite.getname() == itemname:
                return ite
        return None

    def canact(self, currentmoves):
        if currentmoves < int(self.getparam("speed")):
            return True
        return False

    def giveall(self, receiver):
        togive = []
        for ite in self.inventory:
            togive.append(ite)
        for ite in togive:
            self.drop(ite)
            receiver.pick(ite)

    def getbestranged(self):
        bestitem = None
        bestdamage = 0
        if self.getparam("fire") is not None:
            bestitem = item.Item(self.gameengine.iteinfo[self.getparam("fire")], self.gameengine)
        for ite in self.inventory:
            if ite.getparam("damage") is not None and ite.getparam("damage") > bestdamage:
                bestitem = ite
                bestdamage = bestitem.getparam("damage")
        return bestitem


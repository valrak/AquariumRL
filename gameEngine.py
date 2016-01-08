from _ast import mod
from graphicsHandler import GraphicsHandler
import jsonInit
from monster import *
from item import *
from mapField import *
from messageHandler import *
from eventHandler import *
from pygame.locals import *

import pygame
import sys
import pygame.locals as pg
from utils import *

mapmaxx = 0
mapmaxy = 0

PLAYERCREATURE = "diver"
ARENAMAPFILE = "resources/maps/arena1.csv"


mapfield = None
gameevent = None
moninfo = None
mapinfo = None
effinfo = None
iteminfo = None

# todo: melee weapons ?
# todo: pickup interface
# todo: drop interface
# todo: move and shoot traces graphics
# todo: small damage number bubbles in map
# todo: scoring and hiscore
# todo: ui - one liner and diver clock
# todo: config file
# todo: dynamite fuse setting
# todo: dynamite destroys blocks
# todo: remove loop in loop in loop
# todo: map generator - remove isolated caves
# todo: AI - when fired upon, go to the point where fire comes
# todo: AI - recon in corals
# todo: optimize: redraw only when something changed

# fixme: when firing harpoon after firing pearl  File "/home/jaroslav/PyCharm Projects/Arena/gameEngine.py", line 305, in displayinventory
#    items = self.mapfield.getplayer().getinventory(requiredflag)
#AttributeError: 'NoneType' object has no attribute 'getinventory'

class GameEngine(object):
    ALPHABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']

    RESOLUTIONX = 1024
    RESOLUTIONY = 768
    SIZE = (RESOLUTIONX, RESOLUTIONY)
    SCORETABLE = [100, 300]
    turns = 0
    state = "game"
    hiscore = 0
    noscore = False
    itemsgenerated = 0
    clock = pygame.time.Clock()

    def __init__(self):
        # with open(ARENAMAPFILE, 'rb') as csvfile:
        #     csvread = csv.reader(csvfile, delimiter=';', quotechar='"')
        #     arenamap = list(csvread)
        arenamap = None
        self.cursorcoord = (1, 1)
        # data load part
        # jsons
        self.moninfo = jsonInit.loadjson("resources/data/creatures.jsn")
        self.mapinfo = jsonInit.loadjson("resources/data/map.jsn")
        self.effinfo = jsonInit.loadjson("resources/data/effects.jsn")
        self.iteinfo = jsonInit.loadjson("resources/data/items.jsn")

        self.mapfield = MapField(arenamap, self.mapinfo, self.moninfo, self.effinfo, self.iteinfo, self)
        self.mapfield.generatelevel(25, 15)

        self.messagehandler = MessageHandler()
        self.graphicshandler = GraphicsHandler(self)

        self.gameevent = EventHandler()
        self.gameevent.register(self.messagehandler)
        self.gameevent.register(self.graphicshandler)
        self.loop()

        # load hi score

    def initgame(self):
        pygame.init()
        pygame.display.set_caption('Aquarium Arena')
        player = self.generateplayer()

        # introduction messages
        self.gameevent.report("Welcome to Aquarium Arena!", None, None, None)
        self.gameevent.report("Top gladiator score is "+str(self.hiscore)+" points!", None, None, None)
        # main game loop
        player.setparam("level", "3")
        return player

    def generateplayer(self):
        # create list of entities and player entity
        player = Monster(self.moninfo[PLAYERCREATURE], self)
        player.player = True
        player.setposition(self.mapfield.getrandompassable())
        for x in range(0, 5):
            player.pick(Item(self.iteinfo['harpoon'], self))
        player.pick(Item(self.iteinfo['dynamite'], self))
        self.mapfield.addmonster(player)
        return player

    def loop(self):
        player = self.initgame()
        while True:
            for event in pygame.event.get():
                if event.type == pg.QUIT:
                    self.endgame()
                elif event.type == VIDEORESIZE:
                    self.graphicshandler.resize(event.dict['size'])
                else:
                    if self.state == "reset":
                        self.state = "game"
                        self.resetgame()
                        break

                    elif self.state == "look":
                        coord = utils.getcoordsbyevent(event)
                        if coord is not None:
                            self.cursorcoord = (self.cursorcoord[0]+coord[0], self.cursorcoord[1]+coord[1])
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            break
                    elif self.state == "inventory":
                        citem = self.displayinventory()
                        if citem is not None:
                            None
                        else:
                            self.state = "game"
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            break
                    elif self.state == "use":
                        # cancel
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.gameevent.report("Item use cancelled.", None, None, None)
                            break
                        index = self.displayinventory("usable")
                        if index is None:
                            self.gameevent.report("You have nothing usable.", None, None, None)
                        self.state = "game"
                        if index is not None:
                            if len(player.getinventory("usable"))-1 >= index:
                                self.gameevent.report("Using ... " +
                                                      player.getinventory("usable")[index].getname(), None, None, None)
                                player.useitem(player.getinventory("usable")[index])
                                self.passturn()

                    # Firing state
                    elif self.state == "fire":
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.gameevent.report("Firing cancelled.", None, None, None)
                            break
                        coord = utils.getcoordsbyevent(event)
                        if coord is not None:
                            player.fire(coord, player.rangedpreference)
                            self.passturn()
                            if self.state != "reset":
                                self.state = "game"
                        if event.type == pg.KEYDOWN and (event.key == pg.K_i or event.key == pg.K_SPACE):
                            index = self.displayinventory()
                            if index is not None:
                                if len(player.inventory)-1 >= index:
                                    player.rangedpreference = player.inventory[index]
                                    self.gameevent.report("Firing ... " + player.rangedpreference.getname() +
                                                          " Press i or space to change.", None, None, None)
                    # Upgrade mode toggles
                    elif self.state == "upgrade":
                        citem = self.displayupgrades()
                        self.state = "game"
                        if citem is not None:
                            citem.setposition(self.mapfield.getrandompassable())
                            self.mapfield.items.append(citem)

                    # Main mode
                    elif self.state == "game":
                        # Lines
                        coord = utils.getcoordsbyevent(event)
                        if coord is not None:
                            coord = (player.x+coord[0], player.y+coord[1])
                            player.action(coord)
                            self.passturn()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_SPACE or event.key == pg.K_KP5):
                            self.passturn()

                        # Commands
                        # look
                        if event.type == pg.KEYDOWN and (event.key == pg.K_l):
                            self.cursorcoord = self.mapfield.getplayer().getposition()
                            self.state = "look"
                        # inventory
                        if event.type == pg.KEYDOWN and (event.key == pg.K_i):
                            self.state = "inventory"
                        # fire
                        if event.type == pg.KEYDOWN and event.key == pg.K_f:
                            if len(player.inventory) == 0:
                                self.gameevent.report("You have nothing to fire", None, None, None)
                                self.state = "game"
                            elif player.rangedpreference is None:
                                if player.getbestranged() is None:
                                    player.rangedpreference = player.inventory[0]
                                    self.gameevent.report("Firing ... " + player.rangedpreference.getname() +
                                                          " Press i or space to change.", None, None, None)
                                else:
                                    self.gameevent.report("Firing ... "+player.getbestranged().getname() +
                                                          " Press i or space to change.", None, None, None)
                            else:
                                self.gameevent.report("Firing ... "+player.rangedpreference.getname() +
                                                      " Press i or space to change.", None, None, None)
                            self.state = "fire"
                            break
                        # use
                        if event.type == pg.KEYDOWN and event.key == pg.K_u:
                            self.state = "use"
                        if event.type == pg.KEYDOWN and event.key == pg.K_COMMA:
                            # pick up item
                            citems = self.mapfield.getitems(player.getposition())
                            for item in citems:
                                player.pick(item)
                            self.passturn()
                        # todo: delete debug
                        if event.type == pg.KEYDOWN and event.key == pg.K_z:
                            self.state = "upgrade"
            time_passed = self.clock.tick(30)
            self.graphicshandler.drawboard(self.mapfield.terrain)

    def newmap(self):
        self.mapfield.replacemap()

    def resetgame(self):
        self.turns = 0
        self.itemsgenerated = 0
        self.noscore = False

        del self.mapfield
        del self.graphicshandler
        arenamap = None
        self.mapfield = MapField(arenamap, self.mapinfo, self.moninfo, self.effinfo, self.iteinfo, self)
        self.mapfield.generatelevel(25, 15)
        self.graphicshandler = GraphicsHandler(self)

        self.loop()

    def endgame(self):
        pygame.quit()
        sys.exit()

    def passturn(self):
        self.turns += 1

        self.graphicshandler.eraseeventstack()
        self.processeffects()
        for monster in self.mapfield.monsters:
            monster.update()
        for uitem in self.mapfield.items:
            uitem.update()
        for ueffect in self.mapfield.effects:
            ueffect.update()
        self.mapfield.cleanup()
        self.mapfield.generatemonster()
        if self.mapfield.getplayer() is not None:
            if self.mapfield.getplayer().killcount > self.itemsgenerated:
                self.mapfield.generateitem()
                self.itemsgenerated += 1
            # endlevel - no score for kills but more monsters
            if self.noscore is True:
                self.mapfield.generatemonster()
            # next level trigger
            if self.mapfield.getplayer().killcount > 20 and self.noscore is not True:
                self.noscore = True
                self.mapfield.generategate()

    # debug method
    def spawnmonsters(self):
        self.mapfield.addatrandommonster(Monster(self.moninfo[jsonInit.getrandflagged(self.moninfo, "spawner")], self))
        self.mapfield.addspawn("moray eel")

    def processeffects(self):
        for ueffect in self.mapfield.effects:
            if str.startswith(str(ueffect.geteffect()), 'spawn'):
                if ueffect.getspawn() == 'random':
                    self.mapfield.addmonsterat(Monster(self.moninfo[jsonInit.getrandspawn(self.moninfo)], self), ueffect.getposition())
                else:
                    self.mapfield.addmonsterat(Monster(self.moninfo[ueffect.getspawn()], self), ueffect.getposition())

    def displayupgrades(self):
        items = []
        for ite in self.iteinfo:
            params = dict(self.iteinfo[ite])
            if params.has_key("flags"):
                for flag in params["flags"]:
                    if flag == "upgrade":
                        if params.has_key("upgradelevel"):
                            if int(params["upgradelevel"]) <= int(self.mapfield.getplayer().getparam("level")):
                                items.append(Item(self.iteinfo[ite], self))
                        else:
                            items.append(Item(self.iteinfo[ite], self))
        if len(items) == 0:
            return None
        self.graphicshandler.displayitemlist(items)
        loop = True
        while loop:
            for event in pygame.event.get():
                if event.type == pg.KEYDOWN and pygame.key.name(event.key) in self.ALPHABET:
                    return items[self.ALPHABET.index(pygame.key.name(event.key))]  # returns corresponding key alphabet index
                self.clock.tick(30)

    def displayinventory(self, requiredflag=None):
        items = self.mapfield.getplayer().getinventory(requiredflag)
        if len(items) == 0:
            return None
        self.graphicshandler.displayitemlist(items)
        loop = True
        while loop:
            for event in pygame.event.get():
                # cancel
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                    return None
                if event.type == pg.KEYDOWN and pygame.key.name(event.key) in self.ALPHABET:
                    return self.ALPHABET.index(pygame.key.name(event.key))  # returns corresponding key alphabet index
            self.clock.tick(30)
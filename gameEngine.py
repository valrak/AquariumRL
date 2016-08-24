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
from hiscore import *

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

# todo: make explosions animated for better graphical representation of the process (as the monster can enter the
#       explosion tile and do not get hurt (because the explosion was in the last turn and monster entered just the
#       graphical representation, this can confuse the player
# todo: pickup interface
# todo: drop interface
# todo: config file
# todo: dynamite fuse setting
# todo: dynamite destroys blocks
# todo: map generator - remove isolated caves
# todo: AI - when fired upon, go to the point where fire comes
# todo: AI - recon in corals
# todo: optimize: redraw only when something changed
# todo: list of kills

class GameEngine(object):
    ALPHABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']

    RESOLUTIONX = 1024
    RESOLUTIONY = 660
    LASTLEVEL = 10
    SIZE = (RESOLUTIONX, RESOLUTIONY)
    SCORETABLE = [100, 300]
    COMBO_ITEM = 3
    turns = 0
    state = "game"
    hiscore = loadhiscore()
    noscore = False
    lastscore = 0
    lastplayer = None
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

    def initgame(self):
        pygame.init()
        pygame.display.set_caption('Aquarium Arena')
        player = self.generateplayer()

        # introduction messages
        # self.graphicshandler.eraseloglines()
        self.gameevent.report("Welcome to Aquarium Arena!")
        self.gameevent.report("Top gladiator score is "+str(loadhiscore())+" points!")
        # main game loop
        #player.setparam("level", "5")
        return player

    def generateplayer(self):
        # create list of entities and player entity
        player = Monster(self.moninfo[PLAYERCREATURE], self)
        player.player = True
        player.setposition(self.mapfield.getrandompassable())
        for x in range(0, 5):
            player.pick(Item(self.iteinfo['harpoon'], self))
        self.mapfield.addmonster(player)
        return player

    def loop(self):
        player = self.initgame()
        self.draw()
        while True:
            for event in pygame.event.get():
                if event.type == pg.QUIT:
                    self.endgame()
                elif event.type == VIDEORESIZE:
                    self.graphicshandler.resize(event.dict['size'])
                    self.draw()
                else:
                    if self.state == "help":
                        self.deathscreen()
                        self.state = "game"
                        self.draw()
                        break
                    if self.state == "reset":
                        self.deathscreen()
                        self.state = "game"
                        self.gameevent.report("Your score was: "+str(self.lastscore)+".")
                        savehiscore(self.lastscore, self.hiscore)
                        self.resetgame()
                        break
                    elif self.state == "look":
                        coord = utils.getcoordsbyevent(event)
                        if coord is not None:
                            self.cursorcoord = (self.cursorcoord[0]+coord[0], self.cursorcoord[1]+coord[1])
                            self.draw()
                        if event.type == pg.QUIT:
                            self.endgame()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.draw()
                            break
                    elif self.state == "inventory":
                        citem = self.displayinventory()
                        if citem is not None:
                            None
                        else:
                            self.state = "game"
                            self.draw()
                        if event.type == pg.QUIT:
                            self.endgame()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.draw()
                            break
                    elif self.state == "use":
                        # cancel
                        if event.type == pg.QUIT:
                            self.endgame()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.gameevent.report("item use cancelled.")
                            self.draw()
                            break
                        index = self.displayinventory("usable")
                        if index is None:
                            self.gameevent.report("you have nothing usable.")
                            self.draw()
                        self.state = "game"
                        if index is not None:
                            if len(player.getinventory("usable"))-1 >= index:
                                self.gameevent.report("using ... " +
                                                      player.getinventory("usable")[index].getname())
                                player.useitem(player.getinventory("usable")[index])
                                self.passturn()

                    # Firing state
                    elif self.state == "fire":
                        if event.type == pg.QUIT:
                            self.endgame()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.gameevent.report("firing cancelled.")
                            self.draw()
                            break
                        coord = utils.getcoordsbyevent(event)
                        if coord is not None:
                            player.fire(coord, player.rangedpreference)

                            if self.state != "reset":
                                self.state = "game"
                                self.draw()
                            self.passturn()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_i or event.key == pg.K_SPACE):
                            index = self.displayinventory()
                            if index is not None:
                                if len(player.inventory)-1 >= index:
                                    player.rangedpreference = player.inventory[index]
                                    self.gameevent.report("firing " + player.rangedpreference.getname() +
                                                          " press i or space to change.")
                                    self.draw()

                    # Upgrade mode toggles
                    elif self.state == "upgrade":
                        citem = self.displayupgrades()
                        self.state = "game"
                        self.draw()
                        if citem is not None:
                            citem.setposition(self.mapfield.getrandompassable())
                            self.mapfield.items.append(citem)
                            self.draw()

                    # Main mode
                    elif self.state == "game":
                        if event.type == pg.KEYDOWN:
                            self.draw()
                        # Lines
                        coord = utils.getcoordsbyevent(event)
                        if coord is not None:
                            coord = (player.x+coord[0], player.y+coord[1])
                            player.action(coord)
                            self.passturn()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_SPACE or event.key == pg.K_KP5):
                            self.passturn()

                        # Commands
                        # help
                        if event.type == pg.KEYDOWN and (event.key == pg.K_h):
                            self.state = "help"
                            self.draw()
                        # look
                        if event.type == pg.KEYDOWN and (event.key == pg.K_l):
                            self.cursorcoord = self.mapfield.getplayer().getposition()
                            self.state = "look"
                            self.draw()
                        # inventory
                        if event.type == pg.KEYDOWN and (event.key == pg.K_i):
                            self.state = "inventory"
                        # fire
                        if event.type == pg.KEYDOWN and event.key == pg.K_f:
                            if len(player.inventory) == 0:
                                self.gameevent.report("You have nothing to fire")
                                self.state = "game"
                            elif player.rangedpreference is None:
                                if player.getbestranged() is None:
                                    player.rangedpreference = player.inventory[0]
                                    self.gameevent.report("firing " + player.rangedpreference.getname() +
                                                          ". Press i or space to change.")
                                else:
                                    self.gameevent.report("firing " + player.getbestranged().getname() +
                                                          ". Press i or space to change.")
                            else:
                                self.gameevent.report("firing " + player.rangedpreference.getname() +
                                                      ". Press i or space to change.")
                            self.draw()
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
                                self.gameevent.report("picked up a " + item.getname())
                            self.passturn()
            time_passed = self.clock.tick(30)

    def newmap(self):
        self.mapfield.replacemap()

    def resetgame(self):
        self.turns = 0
        self.itemsgenerated = 0
        self.noscore = False

        del self.mapfield
        #del self.graphicshandler
        arenamap = None
        self.mapfield = MapField(arenamap, self.mapinfo, self.moninfo, self.effinfo, self.iteinfo, self)
        self.mapfield.generatelevel(25, 15)
        #self.graphicshandler = GraphicsHandler(self)

        self.loop()

    def draw(self):
        self.graphicshandler.drawboard(self.mapfield.terrain)

    def deathscreen(self):
        loop = True
        while loop:
            for event in pygame.event.get():
                # cancel
                if event.type == pg.KEYDOWN:
                    return None
            self.clock.tick(30)

    def endgame(self):
        pygame.quit()
        sys.exit()

    def passturn(self):
        for ueffect in self.mapfield.effects:
            ueffect.resetupdate()
        self.turns += 1
        self.graphicshandler.eraseeventstack()
        self.processeffects()
        self.mapfield.cleanup()
        for uitem in self.mapfield.items:
            uitem.update()
        for ueffect in self.mapfield.effects:
            if not ueffect.isupdated():
                ueffect.update()
        for monster in self.mapfield.monsters:
            monster.update()
            for ueffect in self.mapfield.effects:
                if not ueffect.isupdated():
                    ueffect.update()
        self.mapfield.cleanup()
        self.mapfield.generatemonster()
        if self.mapfield.getplayer() is not None:
            if self.mapfield.getplayer().killcount > self.itemsgenerated:
                self.mapfield.generateitem()
                self.itemsgenerated += 1
            if self.mapfield.getplayer().combo >= self.COMBO_ITEM:
                self.gameevent.report("Crowds of mermen are cheering and throwing items to arena!")
                self.mapfield.generateitem(True)
            # endlevel - no score for kills but more monsters
            if self.noscore is True:
                self.mapfield.generatemonster()
            # next level trigger
            if self.mapfield.getplayer().killcount >= self.getrequiredkillcount() and self.noscore is not True:
                self.noscore = True
                self.mapfield.generategate()
                self.gameevent.report("GATE IS OPEN! Move through the gate!")
        self.draw()
        self.graphicshandler.pops = []

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
                try:
                    keypressed = pygame.key.name(event.key)
                except AttributeError as e:
                    break
                if event.type == pg.QUIT:
                    self.endgame()
                if event.type == pg.KEYDOWN and keypressed in self.ALPHABET:
                    if len(items) > self.ALPHABET.index(keypressed):
                        return items[self.ALPHABET.index(keypressed)]  # returns corresponding key alphabet index
                self.clock.tick(30)

    def displayinventory(self, requiredflag=None):
        items = self.mapfield.getplayer().getinventory(requiredflag)
        if len(items) == 0:
            return None
        self.graphicshandler.displayitemlist(items)
        loop = True
        while loop:
            for event in pygame.event.get():
                if event.type == pg.QUIT:
                    self.endgame()
                # cancel
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                    return None
                if event.type == pg.KEYDOWN and pygame.key.name(event.key) in self.ALPHABET:
                    return self.ALPHABET.index(pygame.key.name(event.key))  # returns corresponding key alphabet index
            self.clock.tick(30)

    def getrequiredkillcount(self):
        base = 5
        if self.mapfield.getplayer() is not None:
            if self.mapfield.getplayer().getparam("level") is not None:
                base += int(self.mapfield.getplayer().getparam("level")) * 10
        return base

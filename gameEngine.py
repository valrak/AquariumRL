from _ast import mod
from graphicsHandler import GraphicsHandler
import jsonInit
from monster import *
from item import *
from mapField import *
from messageHandler import *
from eventHandler import *

import pygame
import sys
import pygame.locals as pg

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

class GameEngine(object):
    ALPHABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']

    RESOLUTIONX = 1024
    RESOLUTIONY = 768
    SIZE = (RESOLUTIONX, RESOLUTIONY)
    SCORETABLE = [100, 300]
    turns = 0
    firingmode = False
    hiscore = 0
    clock = pygame.time.Clock()

    def __init__(self):
        with open(ARENAMAPFILE, 'rb') as csvfile:
            csvread = csv.reader(csvfile, delimiter=';', quotechar='"')
            arenamap = list(csvread)

        # data load part
        # jsons
        self.moninfo = jsonInit.loadjson("resources/data/creatures.jsn")
        self.mapinfo = jsonInit.loadjson("resources/data/map.jsn")
        self.effinfo = jsonInit.loadjson("resources/data/effects.jsn")
        self.iteinfo = jsonInit.loadjson("resources/data/items.jsn")
        self.mapfield = MapField(arenamap, self.mapinfo, self.moninfo, self.effinfo, self.iteinfo, self)
        #arenamap = self.mapfield.generatelevel(None)
        self.mapfield.terrain = arenamap
        self.messagehandler = MessageHandler()
        self.graphicshandler = GraphicsHandler(arenamap, self)

        self.gameevent = EventHandler()
        self.gameevent.register(self.messagehandler)
        self.gameevent.register(self.graphicshandler)
        self.loop()

        # load hi score

    def loop(self):
        pygame.init()
        pygame.display.set_caption('Aquarium Arena')

        # create list of entities and player entity
        player = Monster(self.moninfo[PLAYERCREATURE], self)
        player.player = True
        player.setposition(self.mapfield.getrandompassable())
        for x in range(0, 5):
            player.pick(Item(self.iteinfo['harpoon'], self))
        player.pick(Item(self.iteinfo['dynamite'], self))
        self.mapfield.addmonster(player)
        # introduction messages
        self.gameevent.report("Welcome to Aquarium Arena!", None, None, None)
        self.gameevent.report("Top gladiator score is "+str(self.hiscore)+" points!", None, None, None)
        # main game loop

        player.setparam("level", "3")


        while True:
            # Main mode
            for event in pygame.event.get():
                if event.type == pg.QUIT:
                    self.endgame()
                else:
                    # Debug
                    if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                        self.mapfield.addrandomspawn()
                    if event.type == pg.KEYDOWN and event.key == pg.K_DELETE:
                        self.mapfield.addatrandommonster(Monster(self.moninfo[jsonInit.getrandflagged(self.moninfo, "spawner")], self))
                    if event.type == pg.KEYDOWN and event.key == pg.K_END:
                        self.mapfield.addatrandomsurfaceitem(Item(self.iteinfo['coin'], self))

                    # Firing mode toggles
                    if self.firingmode is True:
                        # cancel
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE or event.key == pg.K_f):
                            self.firingmode = False
                            self.gameevent.report("Firing cancelled.", None, None, None)
                            break
                        if event.type == pg.KEYDOWN and (event.key == pg.K_i or event.key == pg.K_SPACE):
                            index = self.fireinventory()
                            if index is not None:
                                if len(player.inventory)-1 >= index:
                                    player.rangedpreference = player.inventory[index]
                                    self.gameevent.report("Firing ... " + player.rangedpreference.getname() +
                                                          " Press i or space to change.", None, None, None)

                    # Lines
                    if event.type == pg.KEYDOWN and (event.key == pg.K_UP or event.key == pg.K_KP8):
                        coord = (player.x, player.y-1)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((0, -1), player.rangedpreference)
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_DOWN or event.key == pg.K_KP2):
                        coord = (player.x, player.y+1)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((0, 1), player.rangedpreference)
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_LEFT or event.key == pg.K_KP4):
                        coord = (player.x-1, player.y)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((-1, 0), player.rangedpreference)
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_RIGHT or event.key == pg.K_KP6):
                        coord = (player.x+1, player.y)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((1, 0), player.rangedpreference)
                        else:
                            player.action(coord)
                        self.passturn()

                    # Diagonals
                    if event.type == pg.KEYDOWN and (event.key == pg.K_PAGEUP or event.key == pg.K_KP9):
                        coord = (player.x+1, player.y-1)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((1, -1))
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_HOME or event.key == pg.K_KP7):
                        coord = (player.x-1, player.y-1)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((-1, -1))
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_END or event.key == pg.K_KP1):
                        coord = (player.x-1, player.y+1)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((-1, 1))
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_PAGEDOWN or event.key == pg.K_KP3):
                        coord = (player.x+1, player.y+1)
                        if self.firingmode is True:
                            self.firingmode = False
                            player.fire((1, 1))
                        else:
                            player.action(coord)
                        self.passturn()
                    if event.type == pg.KEYDOWN and (event.key == pg.K_SPACE or event.key == pg.K_KP5):
                        self.passturn()
                    # Commads
                    if event.type == pg.KEYDOWN and event.key == pg.K_f:
                        if player.getbestranged() is None:
                            self.gameevent.report("You have nothing to fire.", None, None, None)
                            break
                        else:
                            if player.rangedpreference is None:
                                self.gameevent.report("Firing ... "+player.getbestranged().getname() +
                                                      " Press i or space to change.", None, None, None)
                            else:
                                self.gameevent.report("Firing ... "+player.rangedpreference.getname() +
                                                      " Press i or space to change.", None, None, None)
                            self.firingmode = True
                            break
                    if event.type == pg.KEYDOWN and event.key == pg.K_COMMA:
                        # pick up item
                        citems = self.mapfield.getitems(player.getposition())
                        for item in citems:
                            player.pick(item)
                        self.passturn()

            time_passed = self.clock.tick(30)
            self.graphicshandler.drawboard()

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
        self.mapfield.generateitem()

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

    def fireinventory(self):
        self.graphicshandler.displayitemlist(self.mapfield.getplayer().inventory)
        loop = True
        while loop:
            for event in pygame.event.get():
                # cancel
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                    return None
                if event.type == pg.KEYDOWN and pygame.key.name(event.key) in self.ALPHABET:
                    return self.ALPHABET.index(pygame.key.name(event.key)) # returns corresponding key alphabet index
            self.clock.tick(30)

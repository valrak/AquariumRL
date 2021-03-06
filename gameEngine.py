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
import math
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
keystrokes = None

class GameEngine(object):
    ALPHABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']

    GATE_MONSTER_RAND_CHANCE = 50

    RESOLUTIONX = 1024
    RESOLUTIONY = 660
    MAPMAXY = 15
    MAPMAXX = 25

    LASTLEVEL = 11
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

    # game settings
    deepblue = 0

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
        self.keystrokes = jsonInit.loadjson("config/keystrokes.jsn")
        self.settings = jsonInit.loadjson("config/settings.jsn")

        self.inventorykey = utils.populatekeys(self.keystrokes.get("inventory"))
        self.numberskey = utils.populatekeys(self.keystrokes.get("numbers"))
        self.standkey = utils.populatekeys(self.keystrokes.get("stand"))
        self.applykey = utils.populatekeys(self.keystrokes.get("apply"))
        self.firekey = utils.populatekeys(self.keystrokes.get("fire"))
        self.examinekey = utils.populatekeys(self.keystrokes.get("examine"))
        self.pickkey = utils.populatekeys(self.keystrokes.get("pick"))
        self.nextkey = utils.populatekeys(self.keystrokes.get("next"))
        self.helpkey = utils.populatekeys(self.keystrokes.get("help"))
        self.confirmkey = utils.populatekeys(self.keystrokes.get("confirm"))
        self.dropkey = utils.populatekeys(self.keystrokes.get("drop"))
        self.upkey = utils.populatekeys(self.keystrokes.get("up"))
        self.downkey = utils.populatekeys(self.keystrokes.get("down"))
        self.leftkey = utils.populatekeys(self.keystrokes.get("left"))
        self.rightkey = utils.populatekeys(self.keystrokes.get("right"))
        self.upleftkey = utils.populatekeys(self.keystrokes.get("upleft"))
        self.downleftkey = utils.populatekeys(self.keystrokes.get("downleft"))
        self.uprightkey = utils.populatekeys(self.keystrokes.get("upright"))
        self.downrightkey = utils.populatekeys(self.keystrokes.get("downright"))

        self.helpscreentext = utils.loadtextfile("resources/texts/helpScreen.txt")
        self.helpboxtext = utils.loadtextfile("resources/texts/helpBox.txt")

        self.mapfield = MapField(arenamap, self.mapinfo, self.moninfo, self.effinfo, self.iteinfo, self)
        self.mapfield.generatelevel(self.MAPMAXX, self.MAPMAXY)

        self.messagehandler = MessageHandler()
        self.graphicshandler = GraphicsHandler(self)

        ratio = self.graphicshandler.correctratio(self.SIZE)

        self.gameevent = EventHandler()
        self.gameevent.register(self.messagehandler)
        self.gameevent.register(self.graphicshandler)
        self.loop()

    def initgame(self):
        # set settings
        self.deepblue = self.settings['deep-blue-effect']

        pygame.init()
        pygame.display.set_caption('Aquarium Arena')
        player = self.generateplayer()

        # introduction messages
        # self.graphicshandler.eraseloglines()
        self.gameevent.report("Welcome to Aquarium Arena!")
        self.gameevent.report("Top gladiator score is "+str(loadhiscore())+" points!")
        # main game loop
        #player.setparam("level", "10")
        return player

    def generateplayer(self):
        # create list of entities and player entity
        player = Monster(self.moninfo[PLAYERCREATURE], self)
        player.player = True
        player.setposition(self.mapfield.getrandompassable())
        for x in range(0, 5):
            player.pick(Item(self.iteinfo['harpoon'], self), True)
        self.mapfield.addmonster(player)
        return player

    def loop(self):
        player = self.initgame()
        self.draw()
        while True:
            for event in pygame.event.get():
                if not self.universalevents(event):
                    if self.state == "help":
                        self.deathscreen()
                        self.state = "game"
                        self.draw()
                        break
                    if self.state == "reset":
                        self.deathscreen()
                        self.state = "game"
                        self.gameevent.report("Your score was: "+str(self.lastscore)+".")
                        if savehiscore(self.lastscore, self.hiscore):
                            self.gameevent.report("New hiscore! Congratulations!")
                        self.resetgame()
                        break
                    elif self.state == "look":
                        self.universalevents(event)
                        coord = self.getcoordsbyevent(event)
                        if coord is not None:
                            self.cursorcoord = (self.cursorcoord[0]+coord[0], self.cursorcoord[1]+coord[1])
                            self.draw()
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.draw()
                            break
                    elif self.state == "inventory":
                        self.universalevents(event)
                        citem = self.displayinventory()
                        if citem is not None:
                            None
                        else:
                            self.state = "game"
                            self.draw()
                        self.universalevents(event)
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.draw()
                            break
                    elif self.state == "drop":
                        self.universalevents(event)
                        # cancel
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.draw()
                            break
                        selecteditems = self.displayselectableinventory()
                        self.draw()
                        self.state = "game"
                        if selecteditems is not None and len(selecteditems) > 0:
                            for droppeditem in selecteditems:
                                amount = selecteditems.get(droppeditem)
                                if droppeditem.isstackable():
                                    if amount > droppeditem.stack or amount == 0:
                                        amount = droppeditem.stack
                                    self.gameevent.report("dropped " + droppeditem.getname() + " " + str(amount) + "x")
                                else:
                                    self.gameevent.report("dropped " + droppeditem.getname())
                                player.drop(droppeditem, amount)
                            self.passturn()
                    elif self.state == "pick":
                        self.universalevents(event)
                        # cancel
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.draw()
                            break
                        sitems = self.mapfield.getitems(player.getposition())
                        if len(sitems) == 1 and (not sitems[0].isstackable() or sitems[0].stack == 1):
                            self.mapfield.getplayer().pick(sitems[0])
                            self.passturn()
                            self.state = "game"
                            self.draw()
                            break
                        selecteditems = self.displayselectableinventory(None, sitems)
                        self.draw()
                        self.state = "game"
                        if selecteditems is not None and len(selecteditems) > 0:
                            for pickeditem in selecteditems:
                                amount = selecteditems.get(pickeditem)
                                player.pick(pickeditem, False, amount)
                            self.passturn()
                    elif self.state == "use":
                        self.universalevents(event)
                        # cancel
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
                        self.universalevents(event)
                        if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                            self.state = "game"
                            self.gameevent.report("firing cancelled.")
                            self.draw()
                            break
                        coord = self.getcoordsbyevent(event)
                        if coord is not None:
                            player.fire(coord, player.rangedpreference)

                            if self.state != "reset":
                                self.state = "game"
                                self.draw()
                            self.passturn()
                        if event.type == pg.KEYDOWN and (event.key in self.inventorykey or event.key == pg.K_SPACE):
                            index = self.displayinventory()
                            if index is not None:
                                if len(player.inventory)-1 >= index:
                                    player.rangedpreference = player.inventory[index]
                                    self.gameevent.report("firing " + player.rangedpreference.getname() +
                                                          ". inventory to change, direction to fire")
                                    self.draw()

                    # Upgrade mode toggles
                    elif self.state == "upgrade":
                        self.universalevents(event)
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
                        # mouselook
                        if event.type == pygame.MOUSEMOTION:
                            currentresx = pygame.display.Info().current_w
                            originalpixelsize = float(currentresx) / float(self.RESOLUTIONX)
                            ex = int(math.ceil(event.pos[0] / originalpixelsize))
                            ey = int(math.ceil(event.pos[1] / originalpixelsize))
                            mousetile = self.graphicshandler.gettileposition((ex, ey))
                            if mousetile is not None and self.graphicshandler.mousetile != mousetile:
                                self.graphicshandler.mousetile = mousetile
                                self.draw()
                        # Lines
                        coord = self.getcoordsbyevent(event)
                        if coord is not None:
                            coord = (player.x+coord[0], player.y+coord[1])
                            player.action(coord)
                            self.passturn()
                        if event.type == pg.KEYDOWN and (event.key in self.standkey):
                            self.passturn()

                        # Commands
                        # help
                        if event.type == pg.KEYDOWN and (event.key in self.helpkey):
                            self.state = "help"
                            self.draw()
                        # look
                        if event.type == pg.KEYDOWN and (event.key in self.examinekey):
                            self.cursorcoord = self.mapfield.getplayer().getposition()
                            self.state = "look"
                            self.draw()
                        # inventory

                        if event.type == pg.KEYDOWN and (event.key in self.inventorykey):
                            self.state = "inventory"
                        # fire
                        if event.type == pg.KEYDOWN and event.key in self.firekey:
                            if len(player.inventory) == 0:
                                self.gameevent.report("You have nothing to fire")
                                self.state = "game"
                            elif player.rangedpreference is None:
                                if player.getbestrangedforplayer() is None:
                                    player.rangedpreference = player.inventory[0]
                                    self.gameevent.report("firing " + player.rangedpreference.getname() +
                                                          ". inventory to change, direction to fire")
                                else:
                                    bestrangedweapon = player.getbestrangedforplayer()
                                    player.rangedpreference = bestrangedweapon
                                    self.gameevent.report("firing " + bestrangedweapon.getname() +
                                                          ". inventory to change, direction to fire")
                            else:
                                self.gameevent.report("firing " + player.rangedpreference.getname() +
                                                      ". inventory to change, direction to fire")
                            self.state = "fire"
                            self.draw()

                            break
                        # use
                        if event.type == pg.KEYDOWN and event.key in self.applykey:
                            self.state = "use"
                        if event.type == pg.KEYDOWN and event.key in self.dropkey:
                            self.state = "drop"
                        if event.type == pg.KEYDOWN and event.key in self.pickkey:
                            # pick up item
                            citems = self.mapfield.getitems(player.getposition())
                            self.state = "pick"
            time_passed = self.clock.tick(30)

    def newmap(self):
        self.mapfield.replacemap()

    def resetgame(self):
        self.turns = 0
        self.itemsgenerated = 0
        self.noscore = False

        del self.mapfield
        arenamap = None
        self.mapfield = MapField(arenamap, self.mapinfo, self.moninfo, self.effinfo, self.iteinfo, self)
        self.mapfield.generatelevel(25, 15)
        self.loop()

    def draw(self):
        self.graphicshandler.drawboard(self.mapfield.terrain)

    def deathscreen(self):
        loop = True
        while loop:
            if self.state == "finallook":
                for event in pygame.event.get():
                    self.universalevents(event)
                    if event.type == pg.KEYDOWN:
                        self.state = "reset"
                self.graphicshandler.drawboard(self.mapfield.terrain)
            else:
                for event in pygame.event.get():
                    if event.type == pg.KEYDOWN and event.key in self.examinekey:
                        self.state = "finallook"
                    elif event.type == pg.KEYDOWN:
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
                if random.randint(0, 100) >= self.GATE_MONSTER_RAND_CHANCE:
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
        lastitem = self.graphicshandler.displayitemlist(items)
        loop = True
        while loop:
            for event in pygame.event.get():
                try:
                    keypressed = pygame.key.name(event.key)
                except AttributeError as e:
                    break
                if event.type == pg.KEYDOWN and event.key in self.nextkey:
                    self.draw()
                    self.graphicshandler.displayitemlist(items, lastitem)
                if event.type == pg.KEYDOWN and keypressed in self.ALPHABET:
                    if len(items) > self.ALPHABET.index(keypressed):
                        return items[self.ALPHABET.index(keypressed)]  # returns corresponding key alphabet index
                self.clock.tick(30)

    def displayinventory(self, requiredflag=None):
        items = self.mapfield.getplayer().getinventory(requiredflag)
        if len(items) == 0:
            return None
        lastitem = self.graphicshandler.displayitemlist(items)
        loop = True
        while loop:
            for event in pygame.event.get():
                self.universalevents(event)
                # cancel
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                    return None
                if event.type == pg.KEYDOWN and event.key in self.nextkey:
                    self.draw()
                    lastitem = self.graphicshandler.displayitemlist(items, lastitem)
                if event.type == pg.KEYDOWN and pygame.key.name(event.key) in self.ALPHABET:
                    return self.ALPHABET.index(pygame.key.name(event.key))  # returns corresponding key alphabet index
            self.clock.tick(30)

    def displayselectableinventory(self, requiredflag=None, inputitems=None):
        if inputitems is None:
            items = self.mapfield.getplayer().getinventory(requiredflag)
        else:
            items = inputitems
        if len(items) == 0:
            return None
        originallastitem = 0
        lastitem = self.graphicshandler.displayitemlist(items)
        loop = True
        selected = {}
        number = ""
        while loop:
            for event in pygame.event.get():
                self.universalevents(event)
                # cancel
                if event.type == pg.KEYDOWN and (event.key == pg.K_ESCAPE):
                    return None
                # pick all
                if event.type == pg.KEYDOWN and (event.key in self.pickkey):
                    for sitem in items:
                        selected[sitem] = 0
                    return selected
                # number handling
                if event.type == pg.KEYDOWN and event.key in self.numberskey:
                    # number larger than two digits, reset it
                    if len(number) >= 2:
                        number = pygame.key.name(event.key)
                    else:
                        number += pygame.key.name(event.key)
                if event.type == pg.KEYDOWN and event.key == pg.K_BACKSPACE:
                    number = ""
                    self.graphicshandler.displaytypednumber(number)
                if number != "":
                    self.graphicshandler.displaytypednumber(number)
                # next page
                if event.type == pg.KEYDOWN and event.key in self.nextkey:
                    self.draw()
                    originallastitem = lastitem
                    lastitem = self.graphicshandler.displayitemlist(items, lastitem, selected)
                # select item
                if event.type == pg.KEYDOWN and pygame.key.name(event.key) in self.ALPHABET:
                    keyindex = self.ALPHABET.index(pygame.key.name(event.key))
                    if keyindex <= len(items) - 1:
                        sitem = items[keyindex]
                        if sitem in selected:
                            selected.pop(sitem)
                        else:
                            if number == "" or number == "0":
                                selected[sitem] = 0
                            else:
                                selected[sitem] = int(number)
                    self.graphicshandler.displayitemlist(items, originallastitem, selected)
                    number = ""
                    #self.graphicshandler.displaytypednumber(number)
                if event.type == pg.KEYDOWN and event.key in self.confirmkey:
                    return selected

            self.clock.tick(30)

    def getrequiredkillcount(self):
        base = 5
        if self.mapfield.getplayer() is not None:
            if self.mapfield.getplayer().getparam("level") is not None:
                base += int(self.mapfield.getplayer().getparam("level")) * 10
        return base

    def getcoordsbyevent(self, event):
        coord = None
        if event.type == pg.KEYDOWN and (event.key in self.upkey):
            coord = (0, -1)
        if event.type == pg.KEYDOWN and (event.key in self.downkey):
            coord = (0, +1)
        if event.type == pg.KEYDOWN and (event.key in self.leftkey):
            coord = (-1, 0)
        if event.type == pg.KEYDOWN and (event.key in self.rightkey):
            coord = (+1, 0)
        # Diagonals
        if event.type == pg.KEYDOWN and (event.key in self.uprightkey):
            coord = (+1, -1)
        if event.type == pg.KEYDOWN and (event.key in self.upleftkey):
            coord = (-1, -1)
        if event.type == pg.KEYDOWN and (event.key in self.downleftkey):
            coord = (-1, +1)
        if event.type == pg.KEYDOWN and (event.key in self.downrightkey):
            coord = (+1, +1)
        return coord

    def universalevents(self, event):
        if event.type == pg.QUIT:
            self.endgame()
        elif event.type == VIDEORESIZE:
            self.graphicshandler.resize(event.dict['size'])
            self.draw()
        return False

import gameEngine

from tileEngine import *
from pygame.locals import *

__author__ = 'Jaroslav'

MAPPOSX = 10
MAPPOSY = 10
TILESIZE = 32
MAXLOGLINES = 5


class GraphicsHandler(object):
    loglines = []
    eventstack = {}
    gameengine = None
    size = None

    def __init__(self, gameengine):
        self.gameengine = gameengine
        self.maptiles = pygame.image.load("resources/img/MapTiles.png")
        self.montiles = pygame.image.load("resources/img/CreatureTiles.png")
        self.efftiles = pygame.image.load("resources/img/EffectTiles.png")
        self.itetiles = pygame.image.load("resources/img/ItemTiles.png")
        self.uitiles = pygame.image.load("resources/img/UI.png")
        self.maptileeng = TileEngine(self.maptiles, gameengine.mapinfo, TILESIZE)
        self.montileeng = TileEngine(self.montiles, gameengine.moninfo, TILESIZE)
        self.efftileeng = TileEngine(self.efftiles, gameengine.effinfo, TILESIZE)
        self.itetileeng = TileEngine(self.itetiles, gameengine.iteinfo, TILESIZE)
        self.uitileeng = TileEngine(self.uitiles, gameengine.iteinfo, TILESIZE)
        self.size = gameengine.SIZE
        self.finalscreen = pygame.display.set_mode(self.size, HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.screen = self.finalscreen.copy()
        pygame.font.init()

    def event(self, thing, name=None, newvalue=None, oldvalue=None):
        if thing == "error":
            self.newlogline(name)
        # fixme: temporary, move to messageHandler!
        if name is not None and newvalue is not None:
            if not newvalue == oldvalue:
                self.newlogline(str(thing.getname() + " changed its " + name + " to " + str(newvalue)))
        if name is None and newvalue is None and oldvalue is None:
            self.newlogline(thing)

    def drawboard(self, arenamap):
        if self.gameengine.mapfield.getplayer is None:
            self.gameengine.state = "reset"
        if self.gameengine.state == "reset":
            return
        self.maplayer = self.maptileeng.getmapsurface(arenamap)
        self.screen.fill(pygame.Color('grey50'))
        self.screen.blit(self.maplayer, (MAPPOSX, MAPPOSY))

        # display all items
        for item in self.gameengine.mapfield.items:
            itemimage = self.itetileeng.gettile(item.parameters["id"])
            self.screen.blit(itemimage, c(item.getvisualpos(TILESIZE)))

        # display all monsters
        for monster in self.gameengine.mapfield.monsters:
            monsterimage = self.montileeng.gettile(monster.parameters["id"])
            self.screen.blit(monsterimage, c(monster.getvisualpos(TILESIZE)))

        # display all effects
        for effect in self.gameengine.mapfield.effects:
            effectimage = self.efftileeng.gettile(effect.parameters["id"])
            self.screen.blit(effectimage, c(effect.getvisualpos(TILESIZE)))

        # Log
        self.font = pygame.font.Font("./resources/fonts/pixelmix.ttf", 20)
        logposadd = 0
        logbackgr = pygame.Surface((700, 150))
        logbackgr = logbackgr.convert()
        logbackgr.fill(pygame.Color("black"))
        for line in self.loglines:
            text = self.font.render(line, 1, (120+logposadd, 120+logposadd, 120+logposadd))
            logbackgr.blit(text, (10, 0+logposadd))
            logposadd += 20
        self.screen.blit(logbackgr, (10, 530))

        # Status
        self.font = pygame.font.Font("./resources/fonts/pixelmix.ttf", 14)
        statusbackgr = pygame.Surface((200, 300))
        statusbackgr = statusbackgr.convert()
        statusbackgr.fill(pygame.Color("black"))
        statusadd = 0
        params = self.gameengine.mapfield.getplayer().parameters
        for param in params:
            text = self.font.render(param+" "+str(params[param]), 1, (pygame.Color("grey70")))
            statusbackgr.blit(text, (5, 5+statusadd))
            statusadd += 20
        self.screen.blit(statusbackgr, (830, 100))

        # Inventory
        invbackgr = pygame.Surface((200, 300))
        invbackgr = invbackgr.convert()
        invbackgr.fill(pygame.Color("black"))
        invadd = 0
        inv = self.gameengine.mapfield.getplayer().inventory
        for item in inv:
            if item.isstackable():
                text = self.font.render(item.getname()+" (x"+str(item.stack)+")", 1, (pygame.Color("grey70")))
            else:
                text = self.font.render(item.getname(), 1, (pygame.Color("grey70")))
            invbackgr.blit(text, (5, 5+invadd))
            invadd += 20
        self.screen.blit(invbackgr, (830, 500))

        # Events
        for key in self.eventstack:
            self.screen.blit(self.eventstack[key], key)

        # Special modes
        if self.gameengine.state == "fire":
            statusbackgr = pygame.Surface((100, 20))
            statusbackgr = statusbackgr.convert()
            text = self.font.render("Firing", 1, (pygame.Color("grey70")))
            statusbackgr.blit(text, (1, 1))
            self.screen.blit(statusbackgr, (830, 20))
        if self.gameengine.state == "look":
            statusbackgr = pygame.Surface((100, 20))
            statusbackgr = statusbackgr.convert()
            text = self.font.render("Looking", 1, (pygame.Color("grey70")))
            statusbackgr.blit(text, (1, 1))
            self.screen.blit(statusbackgr, (830, 20))
            cursorimage = self.uitileeng.getcustomtile(0, 0, 32, 32)
            self.screen.blit(cursorimage, (self.gameengine.cursorcoord[0]*TILESIZE+MAPPOSX,
                                           self.gameengine.cursorcoord[1]*TILESIZE+MAPPOSY))
        self.finalscreen.blit(pygame.transform.scale(self.screen, self.size), (0, 0))
        pygame.display.flip()

    def eraseeventstack(self):
        self.eventstack = {}

    def newlogline(self, logline):
        if len(self.loglines) > MAXLOGLINES:
            self.loglines.pop(0)
        self.loglines.append(logline)

    def displayitemlist(self, itemlist):
        stringlist = []
        i = 0
        for item in itemlist:
            if i >= len(self.gameengine.ALPHABET):
                break
            if item.isstackable():
                stringlist.append(self.gameengine.ALPHABET[i]+") "+item.getname()+" (x"+str(item.stack)+")")
            else:
                stringlist.append(self.gameengine.ALPHABET[i]+") "+item.getname())
            i += 1
        self.displaystringlist(stringlist)

    def displaystringlist(self, stringlist):
        maxy = len(stringlist) * 30
        # count maximum x size by maximal length of string to be printed
        maxx = 100
        for line in stringlist:
            if maxx < len(line)*15:
                maxx = len(line)*15

        invbackgr = pygame.Surface((maxx, maxy), pygame.SRCALPHA)
        invbackgr.fill((0, 0, 0, 128))

        invadd = 0
        inv = self.gameengine.mapfield.getplayer().inventory
        for line in stringlist:
            text = self.font.render(line, 1, (pygame.Color("grey70")))
            invbackgr.blit(text, (5, 5+invadd))
            invadd += 20

        self.screen.blit(invbackgr, (100, 100))
        self.finalscreen.blit(pygame.transform.scale(self.screen, self.size), (0, 0))
        pygame.display.flip()

    # window changed its size
    def resize(self, newsize):
        self.finalscreen = pygame.display.set_mode(newsize, HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.size = newsize

# FIXME: return coordinates to match map position to align to the grid """
c = lambda coords: (coords[0] + MAPPOSX, coords[1] + MAPPOSX)
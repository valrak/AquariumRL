import gameEngine

from tileEngine import *
from pygame.locals import *

MAPPOSX = 10
MAPPOSY = 10
TILESIZE = 32
MAXLOGLINES = 5


class GraphicsHandler(object):
    loglines = []
    eventstack = {}
    pops = []
    gameengine = None
    size = None

    def __init__(self, gameengine):
        self.gameengine = gameengine
        self.maptiles = pygame.image.load("resources/img/MapTiles.png")
        self.montiles = pygame.image.load("resources/img/CreatureTiles.png")
        self.efftiles = pygame.image.load("resources/img/EffectTiles.png")
        self.itetiles = pygame.image.load("resources/img/ItemTiles.png")
        self.uitiles = pygame.image.load("resources/img/UI.png")
        self.uiparts = pygame.image.load("resources/img/watch.png")
        self.maptileeng = TileEngine(self.maptiles, gameengine.mapinfo, TILESIZE)
        self.montileeng = TileEngine(self.montiles, gameengine.moninfo, TILESIZE)
        self.efftileeng = TileEngine(self.efftiles, gameengine.effinfo, TILESIZE)
        self.itetileeng = TileEngine(self.itetiles, gameengine.iteinfo, TILESIZE)
        self.uitileeng = TileEngine(self.uitiles, gameengine.iteinfo, TILESIZE)
        self.uiparttileeng = TileEngine(self.uiparts, gameengine.iteinfo, TILESIZE)
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
        self.screen.fill(pygame.Color('black'))
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
        watchimage = self.uiparttileeng.getcustomtile(0, 0, 168, 315)

        player = self.gameengine.mapfield.getplayer()
        maxhp = str(player.getparam("maxhp"))
        curhp = str(player.getparam("hp"))
        score = str(player.score)
        level = str(player.getparam("level"))

        text = self.font.render("H "+curhp+" / "+maxhp, 1, (pygame.Color("green")))
        watchimage.blit(text, (34, 126))
        text = self.font.render("S "+score, 1, (pygame.Color("green")))
        watchimage.blit(text, (34, 146))
        text = self.font.render("L " + level + " / " +
                                str(self.gameengine.getrequiredkillcount() - player.killcount),
                                1, (pygame.Color("green")))
        watchimage.blit(text, (34, 166))
        self.screen.blit(watchimage, (830, 100))

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
            infotext = self.infoview(self.gameengine.cursorcoord)
            if infotext is not None:
                self.drawwindow(infotext, self.gameengine.cursorcoord)

        self.displaypops()

        self.finalscreen.blit(pygame.transform.scale(self.screen, self.size), (0, 0))
        pygame.display.flip()

    def eraseeventstack(self):
        self.eventstack = {}

    def newlogline(self, logline):
        if len(self.loglines) > MAXLOGLINES:
            self.loglines.pop(0)
        self.loglines.append(logline)

    def displayitemlist(self, itemlist):
        allitemsface = pygame.Surface((1, 1), pygame.SRCALPHA)
        i = 0
        for item in itemlist:
            if i >= len(self.gameengine.ALPHABET):
                break
            if item.isstackable():
                itemface = self.itemdisplay(item, self.gameengine.ALPHABET[i], " (x"+str(item.stack)+")")
            else:
                itemface = self.itemdisplay(item, self.gameengine.ALPHABET[i])
            i += 1
            allitemsface = self.gluebelow(allitemsface, itemface)
        self.drawwindow(allitemsface, (1, 1))
        self.finalscreen.blit(pygame.transform.scale(self.screen, self.size), (0, 0))
        pygame.display.flip()

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

    def pickupview(self, coord):
        #todo
        items = self.gameengine.mapfield.getitems(coord)
        stringlist = []
        # weighttile = self.uitileeng.getcustomtile(0, 64, 16, 16)
        # surface = pygame.Surface((1, 1), pygame.SRCALPHA)
        i = 0
        for item in items:
            if i >= len(self.gameengine.ALPHABET):
                break
            if item.isstackable():
                stringlist.append(self.gameengine.ALPHABET[i]+") "+item.getname()+" (x"+str(item.stack)+")")
            else:
                stringlist.append(self.gameengine.ALPHABET[i]+") "+item.getname())
            i += 1

            # itemsurface = self.font.render(item.getname(), 1, (pygame.Color("blue")))
            # if item.getparam("weight") is not None:
            #     weightface = self.font.render(str(item.getparam("weight")), 1, (pygame.Color("grey70")))
            #     itemsurface = self.glueleft(surface, weightface, 4)
            # surface = self.gluebelow(surface, itemsurface, 2)
        return stringlist

    def itemdisplay(self, item, letter=None, stack=None):
        damagetile = self.uitileeng.getcustomtile(0, 32, 16, 16)
        weighttile = self.uitileeng.getcustomtile(0, 64, 16, 16)
        arrowtile = self.uitileeng.getcustomtile(0, 32+16, 16, 16)
        name = self.font.render(item.getname(), 1, (pygame.Color("lightblue")))
        belowname = pygame.Surface((1, 1), pygame.SRCALPHA)
        if item.getparam("damage") is not None:
            damageface = self.font.render(str(item.getparam("damage")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(damagetile, damageface, 2)
            belowname = self.glueleft(belowname, tempsurface)
        if item.getparam("weight") is not None:
            weightface = self.font.render(str(item.getparam("weight")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(weighttile, weightface, 2)
            belowname = self.glueleft(belowname, tempsurface)
        if item.getparam("range") is not None:
            rangeface = self.font.render(str(item.getparam("range")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(arrowtile, rangeface, 2)
            belowname = self.glueleft(belowname, tempsurface)
        tempsurface = self.gluebelow(name, belowname, 2)
        if letter is not None:
            letterface = self.font.render(letter+") ", 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(letterface, tempsurface)
        return tempsurface

    def infoview(self, coord):
        monster = self.gameengine.mapfield.getoccupants(coord)
        items = self.gameengine.mapfield.getitems(coord)
        effects = self.gameengine.mapfield.geteffects(coord)
        damagetile = self.uitileeng.getcustomtile(0, 32, 16, 16)
        timetile = self.uitileeng.getcustomtile(16, 32+16, 16, 16)
        healthtile = self.uitileeng.getcustomtile(16, 32, 16, 16)
        arrowtile = self.uitileeng.getcustomtile(0, 32+16, 16, 16)
        if monster is None and len(items) == 0 and len(effects) == 0:
            return None
        surface = pygame.Surface((1, 1), pygame.SRCALPHA)
        step = 0
        if monster is not None:
            step = 8
            name = self.font.render(monster.getname(), 1, (pygame.Color("red")))
            attackface = self.font.render(str(monster.getparam("attack")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(damagetile, attackface, 2)
            healthface = self.font.render(str(monster.getparam("hp")), 1, (pygame.Color("grey70")))
            healthface = self.glueleft(healthtile, healthface, 2)
            tempsurface = self.glueleft(healthface, tempsurface, 10)
            if monster.getbestranged() is not None:
                rangedsurface = self.font.render(str(monster.getbestranged().getparam("damage")), 1, (pygame.Color("grey70")))
                rangedsurface = self.glueleft(arrowtile, rangedsurface, 2)
                tempsurface = self.glueleft(tempsurface, rangedsurface, 10)
            surface = self.gluebelow(name, tempsurface, 4)
        for item in items:
            tempsurface = self.itemdisplay(item)
            surface = self.gluebelow(surface, tempsurface, step)
            step = 8
        for effect in effects:
            name = self.font.render(effect.getname(), 1, (pygame.Color("green")))
            belowname = pygame.Surface((1, 1), pygame.SRCALPHA)
            if effect.getparam("damage") is not None:
                damageface = self.font.render(str(effect.getparam("damage")), 1, (pygame.Color("grey70")))
                tempsurface = self.glueleft(damagetile, damageface, 2)
                belowname = self.glueleft(belowname, tempsurface)
            if effect.ttl is not None:
                ttl = effect.ttl
                timeface = self.font.render(str(ttl), 1, (pygame.Color("grey70")))
                tempsurface = self.glueleft(timetile, timeface, 2)
                belowname = self.glueleft(belowname, tempsurface)
            tempsurface = self.gluebelow(name, belowname, 2)
            surface = self.gluebelow(surface, tempsurface, step)
        return surface

    def gluebelow(self, surface1, surface2, step=0):
        surface1size = surface1.get_size()
        surface2size = surface2.get_size()
        if surface1size[0] > surface2size[0]:
            xsurfacesize = surface1size[0]
        else:
            xsurfacesize = surface2size[0]
        surfacesize = (xsurfacesize,
                       surface1size[1] + surface2size[1] + step)
        surface = pygame.Surface(surfacesize, pygame.SRCALPHA)
        surface.blit(surface1, (0, 0))
        surface.blit(surface2, (0, surface1size[1] + step))
        return surface

    def glueleft(self, surface1, surface2, step=0):
        surface1size = surface1.get_size()
        surface2size = surface2.get_size()
        surfacesize = (surface1size[0] + surface2size[0] + step,
                       surface2size[1])
        surface = pygame.Surface(surfacesize, pygame.SRCALPHA)
        surface.blit(surface1, (0, 0))
        surface.blit(surface2, (surface1size[0] + step, 0))
        return surface

    # window changed its size
    def resize(self, newsize):
        self.finalscreen = pygame.display.set_mode(newsize, HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.size = newsize

    def drawwindow(self, drawing, coord):
        step = 50
        size = drawing.get_size()
        size = (size[0] + 6, size[1] + 6)
        x = coord[0] * TILESIZE
        y = coord[1] * TILESIZE
        if size[0] + x > self.size[0]:
            x = x - size[0] - step
        else:
            x += step
        if size[1] + y > self.size[1]:
            y = y - size[1] - step
        else:
            y += step
        coord = (x, y)
        backgr = pygame.Surface((size[0], size[1]))
        backgr = backgr.convert()
        backgr.blit(drawing, (3, 3))
        self.screen.blit(backgr, coord)

    def addpop(self, text, coord, tcolor):
        self.pops.append([text, coord, tcolor])

    def displaypops(self):
        for pop in self.pops:
            coord = pop[1]
            x = coord[0] * TILESIZE + TILESIZE
            y = coord[1] * TILESIZE
            text = pop[0]
            tcolor = pop[2]

            poptext = self.font.render(text, 1, (pygame.Color(tcolor)))
            self.screen.blit(poptext, (x, y))



# FIXME: return coordinates to match map position to align to the grid """
c = lambda coords: (coords[0] + MAPPOSX, coords[1] + MAPPOSX)
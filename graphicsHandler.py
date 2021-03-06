import gameEngine
import effect
import pathfinder
from tileEngine import *
from pygame.locals import *

WATCHPOS = (830, 10)
LOGWINDOWPOS = (10, 500)
LOGWINDOWSIZE = (700, 150)

MAPPOSX = 10
MAPPOSY = 10
TILESIZE = 32
BIGTILESIZE = 50
MAXLOGLINES = 6

bigtilestep = BIGTILESIZE - TILESIZE

class GraphicsHandler(object):
    loglines = []
    eventstack = {}
    pops = []
    gameengine = None
    size = None
    mousetile = None

    def __init__(self, gameengine):
        self.gameengine = gameengine
        self.maptiles = pygame.image.load("resources/img/MapTiles.png")
        self.montiles = pygame.image.load("resources/img/CreatureTiles.png")
        self.bigmontiles = pygame.image.load("resources/img/BigCreatureTiles.png")
        self.efftiles = pygame.image.load("resources/img/EffectTiles.png")
        self.itetiles = pygame.image.load("resources/img/ItemTiles.png")
        self.uitiles = pygame.image.load("resources/img/UI.png")
        self.uiparts = pygame.image.load("resources/img/watch.png")
        self.maptileeng = TileEngine(self.maptiles, gameengine.mapinfo, TILESIZE)
        self.montileeng = TileEngine(self.montiles, gameengine.moninfo, TILESIZE)
        self.bigmontileeng = TileEngine(self.bigmontiles, gameengine.moninfo, BIGTILESIZE)
        self.efftileeng = TileEngine(self.efftiles, gameengine.effinfo, TILESIZE)
        self.itetileeng = TileEngine(self.itetiles, gameengine.iteinfo, TILESIZE)
        self.uitileeng = TileEngine(self.uitiles, gameengine.iteinfo, TILESIZE)
        self.uiparttileeng = TileEngine(self.uiparts, gameengine.iteinfo, TILESIZE)
        self.size = gameengine.SIZE
        self.finalscreen = pygame.display.set_mode(self.size, HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.screen = self.finalscreen.copy()
        pygame.font.init()
        self.popfont = pygame.font.Font("./resources/fonts/FreeMonoBold.ttf", 18)
        self.logfont = pygame.font.Font("./resources/fonts/FreeMonoBold.ttf", 20)
        self.statusfont = pygame.font.Font("./resources/fonts/FreeMonoBold.ttf", 14)
        self.helpfont = pygame.font.Font("./resources/fonts/FreeMonoBold.ttf", 16)
        self.infofont = pygame.font.Font("./resources/fonts/FreeMonoBold.ttf", 16)
        self.underlineinfofont = pygame.font.Font("./resources/fonts/FreeMonoBold.ttf", 16)
        self.underlineinfofont.set_underline(True)

    def event(self, thing, name=None, newvalue=None, oldvalue=None):
        if thing == "error":
            self.newlogline(name)
        # fixme: temporary, move to messageHandler!
        if name is not None and newvalue is not None:
            if not newvalue == oldvalue:
                # self.newlogline(str(thing.getname() + " changed its " + name + " to " + str(newvalue)))
                if thing.getname() == "diver":
                    if name != "hp":
                        self.newlogline("Your "+name+" changed to "+str(newvalue)+"!")
        if name is None and newvalue is None and oldvalue is None:
            self.newlogline(thing)

    def drawboard(self, arenamap):
        self.maplayer = self.maptileeng.getmapsurface(arenamap)
        self.screen.fill(pygame.Color('black'))
        self.screen.blit(self.maplayer, (MAPPOSX, MAPPOSY))

        # display all items
        for item in self.gameengine.mapfield.items:
            itemimage = self.itetileeng.gettile(item.parameters["id"])
            self.screen.blit(itemimage, c(item.getvisualpos(TILESIZE)))

        # display all monsters
        for monster in self.gameengine.mapfield.monsters:
            # huge monsters has another tileset and are huge
            if monster.getflag("huge"):
                monsterimage = self.bigmontileeng.gettile(monster.parameters["id"])
                position = c(monster.getvisualpos(TILESIZE))
                position = (position[0] - bigtilestep / 2, position[1] - bigtilestep / 2)
                self.screen.blit(monsterimage, position)
            else:
                monsterimage = self.montileeng.gettile(monster.parameters["id"])
                self.screen.blit(monsterimage, c(monster.getvisualpos(TILESIZE)))

        # display all effects
        for effect in self.gameengine.mapfield.effects:
            effectimage = self.efftileeng.gettile(effect.parameters["id"])
            self.screen.blit(effectimage, c(effect.getvisualpos(TILESIZE)))

        # Events
        for key in self.eventstack:
            self.screen.blit(self.eventstack[key], key)

        # Special effects
        if self.gameengine.deepblue == 1:
            alpha = 0
            fcolor = (0, 36, 56)
            # if self.gameengine.noscore:
            #     fcolor = (255, 0, 0)
            for y in range(self.maplayer.get_height()):
                s = pygame.Surface((self.maplayer.get_width(), 1))
                s.set_alpha(int(alpha))
                s.fill(fcolor)
                self.screen.blit(s, (MAPPOSX, MAPPOSY + y))
                alpha += 0.2


        # Log
        logposadd = 0
        logbackgr = pygame.Surface(LOGWINDOWSIZE)
        logbackgr = logbackgr.convert()
        logbackgr.fill(pygame.Color("black"))
        for line in self.loglines:
            text = self.logfont.render(line, 1, (120+logposadd, 120+logposadd, 120+logposadd))
            logbackgr.blit(text, (10, 0+logposadd))
            logposadd += 20
        self.screen.blit(logbackgr, LOGWINDOWPOS)

        if self.gameengine.state == "help":
            self.displayhelpscreen()
            self.finalscreen.blit(pygame.transform.smoothscale(self.screen, self.correctratio(self.size)), (0, 0))
            pygame.display.flip()
            return

        if self.gameengine.state == "win":
            player = self.gameengine.mapfield.getplayer()
            self.displaywin(player.score, player.killslist)
            pygame.display.flip()
            return

        if self.gameengine.state == "reset":
            player = self.gameengine.mapfield.getplayer()
            if player is not None and int(player.getparam("level")) >= self.gameengine.LASTLEVEL:
                self.displaywin(player.score, player.killslist)
            else:
                self.displaydeath(str(self.gameengine.lastscore), self.gameengine.lastplayer.killslist)
            self.finalscreen.blit(pygame.transform.smoothscale(self.screen, self.correctratio(self.size)), (0, 0))
            pygame.display.flip()
            return

        if self.gameengine.mapfield.getplayer() is not None:
            # Status
            self.displayhelp()

            watchimage = self.uiparttileeng.getcustomtile(0, 0, 168, 315)

            player = self.gameengine.mapfield.getplayer()
            maxhp = str(player.getparam("maxhp"))
            curhp = str(player.getparam("hp"))
            score = str(player.score)
            level = str(player.getparam("level"))
            combo = str(player.combo)

            maxweight = str(player.getparam("weight limit"))
            weight = str(player.gettotalweight())

            tcolor = "green"
            if (int(curhp) - int(maxhp) / 5) <= 0:
                tcolor = "red"
            text = self.statusfont.render("H "+curhp+" / "+maxhp, 1, (pygame.Color(tcolor)))
            watchimage.blit(text, (40, 113))
            text = self.statusfont.render("S "+score, 1, (pygame.Color("green")))
            watchimage.blit(text, (40, 133))

            tcolor = "green"
            if (self.gameengine.getrequiredkillcount() - player.killcount) <= 0:
                tcolor = "red"
            text = self.statusfont.render("L " + level + " / " +
                                    str(self.gameengine.getrequiredkillcount() - player.killcount),
                                    1, (pygame.Color(tcolor)))
            watchimage.blit(text, (40, 153))

            tcolor = "green"
            if int(weight) > int(maxweight):
                tcolor = "red"
            text = self.statusfont.render("W " + weight + " / " + maxweight, 1, (pygame.Color(tcolor)))
            watchimage.blit(text, (40, 173))

            tcolor = "green"
            if int(combo) >= self.gameengine.COMBO_ITEM:
                tcolor = "red"
            text = self.statusfont.render("C " + combo, 1, (pygame.Color(tcolor)))
            watchimage.blit(text, (64, 193))

            self.screen.blit(watchimage, WATCHPOS)

            # Special modes
            if self.gameengine.state == "fire":
                statusbackgr = pygame.Surface((100, 20))
                statusbackgr = statusbackgr.convert()
                text = self.statusfont.render("Firing", 1, (pygame.Color("grey70")))
                # display fire range
                pointerimage = self.uitileeng.getcustomtile(32, 0, 32, 32)
                weapon = self.gameengine.mapfield.getplayer().rangedpreference
                wrange = None
                if weapon is not None:
                    wrange = self.gameengine.mapfield.getplayer().rangedpreference.getparam("range")
                possible = []
                if wrange is not None:
                    for direction in pathfinder.neighbors:
                        temppos = self.gameengine.mapfield.getplayer().getposition()
                        for i in range(0, wrange):
                            if weapon.getflag("beam"):
                                if weapon.geteffect() is not None:
                                    temppos = pathfinder.alterposition(temppos, direction)
                                    # if weapon hits obstacle
                                    if not self.gameengine.mapfield.isnonsolid(temppos):
                                        break
                                    possible.append(temppos)
                            else:
                                oldpos = temppos
                                temppos = pathfinder.alterposition(temppos, direction)
                                monsterat = self.gameengine.mapfield.getoccupants(temppos)
                                if not self.gameengine.mapfield.isnonsolid(temppos):
                                    possible.append(oldpos)
                                    break
                                # if weapon hits any monster
                                if monsterat is not None:
                                    possible.append(temppos)
                                    break
                                # if weapon hits obstacle
                                elif not self.gameengine.mapfield.ispassable(temppos):
                                    break
                                # if not, it flies to its maximum range
                                else:
                                    if i == wrange-1:
                                        possible.append(temppos)
                for location in possible:
                    self.screen.blit(pointerimage, (location[0]*TILESIZE+MAPPOSX,
                                                    location[1]*TILESIZE+MAPPOSY))
                statusbackgr.blit(text, (1, 1))
                self.screen.blit(statusbackgr, (830, 20))
            if self.gameengine.state == "look":
                statusbackgr = pygame.Surface((100, 20))
                statusbackgr = statusbackgr.convert()
                text = self.statusfont.render("Looking", 1, (pygame.Color("grey70")))
                statusbackgr.blit(text, (1, 1))
                self.screen.blit(statusbackgr, (830, 20))
                cursorimage = self.uitileeng.getcustomtile(0, 0, 32, 32)
                self.screen.blit(cursorimage, (self.gameengine.cursorcoord[0]*TILESIZE+MAPPOSX,
                                               self.gameengine.cursorcoord[1]*TILESIZE+MAPPOSY))
                infotext = self.infoview(self.gameengine.cursorcoord)
                if infotext is not None:
                    self.drawwindow(infotext, self.gameengine.cursorcoord)
            else:
                if self.mousetile is not None:
                    infotext = self.infoview(self.mousetile)
                    if infotext is not None:
                        self.drawwindow(infotext, self.mousetile)
            self.displaypops()
        self.finalscreen.blit(pygame.transform.smoothscale(self.screen, self.correctratio(self.size)), (0, 0))
        pygame.display.flip()

    def eraseeventstack(self):
        self.eventstack = {}

    def newlogline(self, logline):
        if len(self.loglines) > MAXLOGLINES:
            self.loglines.pop(0)
        self.loglines.append(logline)

    def displaytypednumber(self, number):
        if number != "" or number != '0':
            numbers = pygame.Surface((23, 23))
            numbers = numbers.convert()
            numbers.fill(pygame.Color("black"))
            text = self.helpfont.render(number, 1, (200, 200, 200))
            numbers.blit(text, (2, 2))
            self.screen.blit(numbers, (55, 82))
            self.finalscreen.blit(pygame.transform.smoothscale(self.screen, self.correctratio(self.size)), (0, 0))
            pygame.display.flip()

    def displayitemlist(self, itemlist, fromitem=0, selected=None):
        self.drawboard(self.gameengine.mapfield.terrain)
        self.displayadvancedhelp(['number - amount', 'letter - item', 'enter - confirm', '_p_ or _,_ - all', 'space - next page', 'escape - cancel'])
        allitemsface = pygame.Surface((1, 1), pygame.SRCALPHA)
        i = 0
        lastitem = 0
        if fromitem >= len(itemlist):
            fromitem = 0
        for item in itemlist:
            addendum = ""
            underscore = None
            if fromitem > lastitem:
                lastitem += 1
                i += 1
                continue
            if i >= len(self.gameengine.ALPHABET):
                break
            if selected is not None and item in selected:
                amount = selected.get(item)
                if amount > item.stack:
                    amount = item.stack
                if amount > 0:
                    addendum = " - " + str(amount) + "x "
                underscore = True
            if item.isstackable():
                itemface = self.itemdisplay(item, self.gameengine.ALPHABET[i], underscore, addendum)
            else:
                itemface = self.itemdisplay(item, self.gameengine.ALPHABET[i], underscore, addendum)
            i += 1
            lastitem += 1
            allitemsface = self.gluebelow(allitemsface, itemface)
            if (allitemsface.get_height() > int(self.gameengine.RESOLUTIONX / 2)) and len(itemlist) > lastitem:
                pageinfo = self.infofont.render("space - next page", 1, (pygame.Color("lightgreen")))
                allitemsface = self.gluebelow(allitemsface, pageinfo)
                break
        if selected is not None:
            pageinfo = self.infofont.render("enter - confirm", 1, (pygame.Color("lightgreen")))
            allitemsface = self.gluebelow(allitemsface, pageinfo)

        self.drawwindow(allitemsface, (1, 1))
        self.finalscreen.blit(pygame.transform.smoothscale(self.screen, self.correctratio(self.size)), (0, 0))
        pygame.display.flip()
        return lastitem

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
            text = self.infofont.render(line, 1, (pygame.Color("grey70")))
            invbackgr.blit(text, (5, 5+invadd))
            invadd += 20

        self.screen.blit(invbackgr, (100, 100))
        self.finalscreen.blit(pygame.transform.smoothscale(self.screen, self.correctratio(self.size)), (0, 0))
        pygame.display.flip()

    def itemdisplay(self, item, letter=None, fontflag=None, addendum=""):
        weighttile = self.uitileeng.getcustomtile(0, 64, 16, 16)
        arrowtile = self.uitileeng.getcustomtile(0, 32+16, 16, 16)
        timetile = self.uitileeng.getcustomtile(16, 32 + 16, 16, 16)
        rangetile = self.uitileeng.getcustomtile(16, 32 + 32, 16, 16)
        textname = item.getname() + addendum
        textdesc = item.getparam("description")
        if item.isstackable():
            if item.stack > 1:
                textname = textname + "("+str(item.stack)+"x)"
        if fontflag is None:
            name = self.infofont.render(textname, 1, (pygame.Color("lightblue")))
        else:
            name = self.underlineinfofont.render(textname, 1, (pygame.Color("lightblue")))
        belowname = pygame.Surface((1, 1), pygame.SRCALPHA)

        if item.getfinalitemdamage() is not None:
            damageface = self.infofont.render(str(item.getfinalitemdamage()), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(arrowtile, damageface, 2)
            belowname = self.glueleft(belowname, tempsurface)

        if item.getparam("weight") is not None:
            weightface = self.infofont.render(str(item.getparam("weight")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(weighttile, weightface, 2)
            belowname = self.glueleft(belowname, tempsurface)
        if item.getparam("range") is not None:
            rangeface = self.infofont.render(str(item.getparam("range")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(rangetile, rangeface, 2)
            belowname = self.glueleft(belowname, tempsurface)
        if item.getparam("fuse") is not None and int(item.getparam("fuse")) > -1:
            fuseface = self.infofont.render(str(item.getparam("fuse")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(timetile, fuseface, 2)
            belowname = self.glueleft(belowname, tempsurface)

        tempsurface = self.gluebelow(name, belowname, 2)
        if textdesc is not None:
            desc = self.infofont.render(textdesc, 1, (pygame.Color("grey40")))
            tempsurface = self.gluebelow(tempsurface, desc)
        if letter is not None:
            letterface = self.infofont.render(letter+") ", 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(letterface, tempsurface)
        return tempsurface

    def infoview(self, coord):
        monster = self.gameengine.mapfield.getoccupants(coord)
        items = self.gameengine.mapfield.getitems(coord)
        effects = self.gameengine.mapfield.geteffects(coord)
        # nothing to display
        if monster is None and len(items) == 0 and len(effects) == 0:
            return None

        damagetile = self.uitileeng.getcustomtile(0, 32, 16, 16)
        timetile = self.uitileeng.getcustomtile(16, 32+16, 16, 16)
        healthtile = self.uitileeng.getcustomtile(16, 32, 16, 16)
        arrowtile = self.uitileeng.getcustomtile(0, 32+16, 16, 16)
        rangetile = self.uitileeng.getcustomtile(16, 32+32, 16, 16)
        surface = pygame.Surface((1, 1), pygame.SRCALPHA)
        step = 0
        if monster is not None:
            step = 8
            name = self.infofont.render(monster.getname(), 1, (pygame.Color("red")))
            attackface = self.infofont.render(str(monster.getparam("attack")), 1, (pygame.Color("grey70")))
            tempsurface = self.glueleft(damagetile, attackface, 2)
            healthface = self.infofont.render(str(monster.getparam("hp")), 1, (pygame.Color("grey70")))
            healthface = self.glueleft(healthtile, healthface, 2)
            tempsurface = self.glueleft(healthface, tempsurface, 10)
            if monster.getbestranged() is not None:
                rangedsurface = self.infofont.render(str(monster.getbestranged().getfinalitemdamage()), 1, (pygame.Color("grey70")))
                rangedsurface = self.glueleft(arrowtile, rangedsurface, 2)
                tempsurface = self.glueleft(tempsurface, rangedsurface, 10)
                rangedsurface = self.infofont.render(str(monster.getbestranged().getparam("range")), 1, (pygame.Color("grey70")))
                rangedsurface = self.glueleft(rangetile, rangedsurface, 2)
                tempsurface = self.glueleft(tempsurface, rangedsurface, 10)
            textdesc = monster.getparam("description")
            if textdesc is not None:
                descsurface = self.infofont.render(textdesc, 1, (pygame.Color("grey40")))
                tempsurface = self.gluebelow(tempsurface, descsurface)
            if not monster.player and len(monster.getinventory()) > 0:
                descsurface = self.infofont.render("items:", 1, (pygame.Color("grey60")))
                tempsurface = self.gluebelow(tempsurface, descsurface)
                for mitem in monster.getinventory():
                    descsurface = self.infofont.render(" "+mitem.getname(), 1, (pygame.Color("grey60")))
                    tempsurface = self.gluebelow(tempsurface, descsurface)
            surface = self.gluebelow(name, tempsurface, 4)
        for item in items:
            tempsurface = self.itemdisplay(item)
            surface = self.gluebelow(surface, tempsurface, step)
            step = 8
        for effect in effects:
            name = self.infofont.render(effect.getname(), 1, (pygame.Color("green")))
            belowname = pygame.Surface((1, 1), pygame.SRCALPHA)
            if effect.getparam("damage") is not None:
                damageface = self.infofont.render(str(effect.getparam("damage")), 1, (pygame.Color("grey70")))
                tempsurface = self.glueleft(damagetile, damageface, 2)
                belowname = self.glueleft(belowname, tempsurface)
            if effect.ttl is not None:
                ttl = effect.ttl
                timeface = self.infofont.render(str(ttl), 1, (pygame.Color("grey70")))
                tempsurface = self.glueleft(timetile, timeface, 2)
                belowname = self.glueleft(belowname, tempsurface)
            textdesc = effect.getparam("description")
            tempsurface = self.gluebelow(name, belowname, 2)
            if textdesc is not None:
                descsurface = self.infofont.render(textdesc, 1, (pygame.Color("grey40")))
                tempsurface = self.gluebelow(tempsurface, descsurface)
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

    def gettileposition(self, windowcoord):
        x = windowcoord[0]
        y = windowcoord[1]
        x -= MAPPOSX
        y -= MAPPOSY
        x /= TILESIZE
        y /= TILESIZE
        if x >= 0 and x < self.gameengine.MAPMAXX and y >= 0 and y < self.gameengine.MAPMAXY:
            return x, y

    def drawwindow(self, drawing, coord, realcoord=False):
        step = 50
        size = drawing.get_size()
        size = (size[0] + 6, size[1] + 6)
        if realcoord:
            x = coord[0]
            y = coord[1]
        else:
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

        if (x + size[0]) >= self.gameengine.RESOLUTIONX:
            x -= x + size[0] - self.gameengine.RESOLUTIONX
        if (y + size[1]) >= self.gameengine.RESOLUTIONY:
            y -= y + size[1] - self.gameengine.RESOLUTIONY

        coord = (x, y)
        backgr = pygame.Surface((size[0], size[1]))
        backgr = backgr.convert()
        backgr.blit(drawing, (3, 3))
        self.screen.blit(backgr, coord)

    def addpop(self, number, coord):
        for pop in self.pops:
            if coord == pop[1]:
                oldnumber = int(pop[0])
                newnumber = int(number)
                newnumber = oldnumber + newnumber
                if newnumber == 0:
                    self.pops.remove(pop)
                pop[0] = newnumber
                return True
        if int(number) != 0:
            self.pops.append([number, coord])

    def displaypops(self):
        for pop in self.pops:
            coord = pop[1]
            x = (coord[0] * TILESIZE + TILESIZE) - TILESIZE/6
            y = (coord[1] * TILESIZE) + TILESIZE/6
            text = pop[0]

            playercoord = self.gameengine.mapfield.getplayer().getposition()
            popcolor = "yellow2"
            if coord == playercoord:
                popcolor = "cyan"
            poptext = self.popfont.render(str(text), 1, (pygame.Color(popcolor)))
            self.screen.blit(poptext, (x, y))

    def erasepops(self):
        self.pops = []

    def displaydeath(self, score, killlist):
        kills = self.killliststrings(killlist)
        deathlines = []
        deathlines.append("")
        deathlines.append(" You are dead.")
        deathlines.append("")
        deathlines.append(" Score: " + str(score))
        if kills is not None:
            deathlines.append("")
            deathlines.append(" Kill list: ")
            for kill in kills:
                deathlines.append("  " + kill)
        deathlines.append("")
        deathlines.append(" Press 'x' to look on the final screen.")
        deathlines.append(" Press any key to continue.")

        tempsurface = pygame.Surface((1, 1), pygame.SRCALPHA)
        for line in deathlines:
            linesurface = self.logfont.render(line, 1, (pygame.Color("grey80")))
            tempsurface = self.gluebelow(tempsurface, linesurface)
        self.drawwindow(tempsurface, (1, 1))

    def displaywin(self, score, killlist):
        kills = self.killliststrings(killlist)
        deathlines = []
        deathlines.append("")
        deathlines.append(" Congratulations! ")
        deathlines.append(" Tritons set you free.")
        deathlines.append(" You've won the game!")
        deathlines.append("")
        deathlines.append(" Score: " + str(score))
        if kills is not None:
            deathlines.append("")
            deathlines.append(" Kill list: ")
            for kill in kills:
                deathlines.append("  " + kill)
        deathlines.append("")
        deathlines.append(" Press 'x' to look on the final screen.")
        deathlines.append(" Press any key to continue.")

        tempsurface = pygame.Surface((1, 1), pygame.SRCALPHA)
        for line in deathlines:
            linesurface = self.logfont.render(line, 1, (pygame.Color("grey80")))
            tempsurface = self.gluebelow(tempsurface, linesurface)
        self.drawwindow(tempsurface, (1, 1))

    def killliststrings(self, killlist):
        if len(killlist) == 0:
            return None
        result = []
        for monster in killlist:
            amount = str(killlist[monster])
            result.append(amount + " of " + monster)
        return result

    def displayhelp(self):
        helplines = self.gameengine.helpboxtext
        logposadd = 0
        logbackgr = pygame.Surface((200, 200))
        logbackgr = logbackgr.convert()
        logbackgr.fill(pygame.Color("black"))
        for line in helplines:
            text = self.helpfont.render(line, 1, (200, 200, 200))
            logbackgr.blit(text, (10, 0 + logposadd))
            logposadd += 20
        self.screen.blit(logbackgr, (830, 440))

    def displayadvancedhelp(self, advhelplines):
        tempsurface = pygame.Surface((1, 1), pygame.SRCALPHA)
        for line in advhelplines:
            linesurface = self.helpfont.render(line, 1, (pygame.Color("grey80")))
            tempsurface = self.gluebelow(tempsurface, linesurface)
        self.drawwindow(tempsurface, (788, 277), True)
        pygame.display.flip()

    def displayhelpscreen(self):
        helplines = self.gameengine.helpscreentext
        logposadd = 0
        logbackgr = pygame.Surface((900, 490))
        logbackgr = logbackgr.convert()
        logbackgr.fill(pygame.Color("black"))
        for line in helplines:
            text = self.helpfont.render(line, 1, (200, 200, 200))
            logbackgr.blit(text, (10, 0 + logposadd))
            logposadd += 20
        helpimage = pygame.image.load('resources/img/helpscreen.png')
        logbackgr = self.gluebelow(logbackgr, helpimage)
        self.screen.blit(logbackgr, (5, 5))
        pygame.display.flip()

    def eraseloglines(self):
        self.loglines = []

    def correctratio(self, size):
        originalx = self.gameengine.RESOLUTIONX
        originaly = self.gameengine.RESOLUTIONY
        originalratio = float(originalx) / float(originaly)
        x = size[0]
        y = size[1]
        y = x / originalratio
        return int(x), int(y)

# FIXME: return coordinates to match map position to align to the grid """
c = lambda coords: (coords[0] + MAPPOSX, coords[1] + MAPPOSX)
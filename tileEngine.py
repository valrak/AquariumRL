import pygame
import csv


class TileEngine(object):
    def __init__(self, tileset, tileinfo, tilesize):
        self.tileSet = tileset
        self.tileInfo = tileinfo
        # size of tiles
        self.SIZE = tilesize

    # get single tile
    # input tileFile, location x starting from 0, location y starting from 0
    def gettile(self, tilename):
        # obtain coordinates from json file
        pos = self.tileInfo[tilename]["tile"]
        coord = str.split(str(pos), ',')
        # create new surface
        tile = pygame.Surface((self.SIZE, self.SIZE))
        # paste to (0,0 top left corner)
        tile.blit(self.tileSet, (0, 0), (int(coord[0])*self.SIZE, int(coord[1])*self.SIZE, self.SIZE, self.SIZE))
        #tile.blit(self.tileSet, (0, 0), (0, 0, 32, 32))
        tile.set_colorkey(pygame.Color("black"))
        return tile

    # get whole map
    def getmapsurface(self, mapfile):
        y = 0
        ytiles = 0

        for row in mapfile:
            ytiles += 1
        xtiles = len(row)
        maplayer = pygame.Surface((xtiles*self.SIZE, ytiles*self.SIZE))

        for row in mapfile:
            x = 0
            for pos in row:
                tile = self.gettile(pos)
                maplayer.blit(tile, (x*self.SIZE, y*self.SIZE))
                x += 1
            y += 1
        return maplayer
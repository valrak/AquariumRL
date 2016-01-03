import random
import pygame.locals as pg

def getrandomdelta(max):
    if random.randint(0, 1) == 1:
        return random.randint(0, max)
    else:
        return -random.randint(0, max)


def getcoordsbyevent(event):
    coord = None
    if event.type == pg.KEYDOWN and (event.key == pg.K_UP or event.key == pg.K_KP8):
        coord = (0, -1)
    if event.type == pg.KEYDOWN and (event.key == pg.K_DOWN or event.key == pg.K_KP2):
        coord = (0, +1)
    if event.type == pg.KEYDOWN and (event.key == pg.K_LEFT or event.key == pg.K_KP4):
        coord = (-1, 0)
    if event.type == pg.KEYDOWN and (event.key == pg.K_RIGHT or event.key == pg.K_KP6):
        coord = (+1, 0)
    # Diagonals
    if event.type == pg.KEYDOWN and (event.key == pg.K_PAGEUP or event.key == pg.K_KP9):
        coord = (+1, -1)
    if event.type == pg.KEYDOWN and (event.key == pg.K_HOME or event.key == pg.K_KP7):
        coord = (-1, -1)
    if event.type == pg.KEYDOWN and (event.key == pg.K_END or event.key == pg.K_KP1):
        coord = (-1, +1)
    if event.type == pg.KEYDOWN and (event.key == pg.K_PAGEDOWN or event.key == pg.K_KP3):
        coord = (+1, +1)
    return coord

class Node(object):
    coord = ()
    g = 0
    h = 0
    parent = None
    passable = 0

    def f(self):
        return self.g + self.h

    def __init__(self, passable, coord):
        self.coord = coord
        self.passable = passable

    def __repr__(self):
        return str(str(self.coord[0])+" "+str(self.coord[1])+" pass="+str(self.passable)+" g="+str(self.g)+" h="+str(self.h),)

neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

openlist = set()
closedlist = set()


def drawline(startcoord, endcoord):
    return abs(endcoord[0] - startcoord[0]) + abs(endcoord[1] - startcoord[1])

def lowest(iset):
    low = None
    ilow = None
    for i in iset:
        f = i.g + i.h
        if low is None or f < low:
            low = f
            ilow = i
    return ilow


def tracepath(node, startcoord):
    if node.parent is None:
        return None
    if node.parent.coord == startcoord:
        return node.coord
    else:
        return tracepath(node.parent, startcoord)


def returnneighbor(nodemap, nx, ny):
    try:
        return nodemap[ny][nx]
    except IndexError:
        return Node(0, (nx, ny))


def findpath(nodemap, startcoord, endcoord):
    # set the destination as passable as destination is always something on map
    nodemap[endcoord[1]][endcoord[0]].passable = 1

    # performance fix: find if the endcoord are not blocked by neighbours
    opened = False
    for xy in neighbors:
        ny = endcoord[1] + xy[1]
        nx = endcoord[0] + xy[0]
        nnode = returnneighbor(nodemap, nx, ny)
        if nnode.coord == startcoord:
            return endcoord
        if nnode.passable is not 0:
            opened = True
    if opened is False:
        return None

    x = startcoord[0]
    y = startcoord[1]

    openlist = set()
    closedlist = set()

    current = nodemap[y][x]
    openlist.add(current)

    while len(openlist) is not 0:
        if lowest(openlist) is nodemap[endcoord[1]][endcoord[0]]:
            return tracepath(lowest(openlist), startcoord)
        current = lowest(openlist)
        x = current.coord[0]
        y = current.coord[1]

        closedlist.add(current)
        openlist.remove(current)

        for xy in neighbors:
            ny = y + xy[1]
            nx = x + xy[0]
            nnode = returnneighbor(nodemap, nx, ny)
            if nnode.passable is not 0:
                cost = current.g + 1
                nnode.f = drawline((nx, ny), endcoord)
                if nnode in openlist and cost < nnode.g:
                    openlist.remove(nnode)
                if nnode not in openlist and nnode not in closedlist:
                    nnode.g = cost
                    nnode.h = drawline((nx, ny), endcoord)
                    openlist.add(nnode)
                    nnode.parent = current
    return None

# lovefully taken from roguebasin, possibly replace with own version
def lineto(start, end):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]
    points = []
    issteep = abs(y2 - y1) > abs(x2 - x1)
    if issteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True
    deltax = x2 - x1
    deltay = abs(y2 - y1)
    error = int(deltax / 2)
    y = y1
    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if issteep:
            points.append((y, x))
        else:
            points.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        points.reverse()
    return points


# checks if the coordinates are besides
def isnear(coord, newcoord):
    if (abs(coord[0] - newcoord[0]) == 1 or abs(coord[0] - newcoord[0]) == 0) and \
            (abs(coord[1] - newcoord[1]) == 1 or abs(coord[1] - newcoord[1]) == 0):
        return True
    return False


# alters position to given coordinates, for example to (0, -1) alters one step north
def alterposition(coord, alteration):
    newx = coord[0] + alteration[0]
    newy = coord[1] + alteration[1]
    return (newx, newy)


# returns direction to the target, in one of 9 ways, if any
def finddirection(coord, target):
    if coord == target: None
    if coord[0] - target[0] == 0:
        if coord[1] < target[1]: return (0, 1)
        else: return (0, -1)
    if coord[1] - target[1] == 0:
        if coord[0] < target[0]: return (1, 0)
        else: return (-1, 0)
    if abs(coord[0] - target[0]) == abs(coord[1] - target[1]):
        if coord[0] < target[0]:
            if coord[1] < target[1]: return (1, 1)
            else: return (1, -1)
        else:
            if coord[1] < target[1]: return (-1, 1)
            else: return (-1, -1)
    return None
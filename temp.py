class Temp(object):
    def __init__(self, coord):
        self.coord = coord
    def getvisualpos(self):
        return self.coord[0]*32+10, self.coord[1]*32+10
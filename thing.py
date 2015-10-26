__author__ = 'Jaroslav'

# interface
class Thing(object):
    def getname(self):
        raise NotImplementedError

    def getposition(self):
        raise NotImplementedError

    def getparam(self, name):
        raise NotImplementedError

    def setparam(self, param, newvalue):
        raise NotImplementedError

    def getvisualpos(self, tilesize):
        return self.x*tilesize, self.y*tilesize
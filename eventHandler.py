__author__ = 'Jaroslav'


class EventHandler(object):
    listeners = []
    debugmode = True

    def register(self, object):
        self.listeners.append(object)

    def report(self, thing, name=None, newvalue=None, oldvalue=None):
        for listener in self.listeners:
            listener.event(thing, name, newvalue, oldvalue)

    def debug(self, thing, name, newvalue, oldvalue):
        if self.debugmode is True:
            for listener in self.listeners:
                listener.event(thing, name, newvalue, oldvalue)
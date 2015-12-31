import random

def getrandomdelta(max):
    if random.randint(0, 1) == 1:
        return random.randint(0, max)
    else:
        return -random.randint(0, max)
def loadhiscore():
    try:
        with open('hiscore', 'r') as f:
            hiscore = f.readline()
            f.close()
    except IOError as e:
        return 0
    return hiscore


def savehiscore(score, hiscore):
    if score == '':
        score = 0
    if hiscore == '':
        hiscore = 0
    if int(hiscore) < int(score):
        with open('hiscore', 'w') as f:
            f.write(str(score))
            f.close()

    return True
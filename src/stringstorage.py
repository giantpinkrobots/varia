def setstrings_linux():
    import gettext
    global strings
    strings = gettext.gettext

def setstrings_win(gettext):
    global strings
    strings = gettext

def gettext(string):
    return strings(string)
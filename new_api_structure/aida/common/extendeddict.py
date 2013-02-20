class ExtendedDict(dict):
    """
    This class internally stores values in a dictionary, but exposes
    the keys also as attributes, i.e. asking for
    ed.key
    will return the value of ed['key'] and so on.
    """
    pass

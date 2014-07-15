__version__ = (0,1,0)

VERSION = __version__

def get_version():
    """
    Very simple function to get a string with the version number.
    """
    return "{}.{}.{}".format(__version__[0], 
                             __version__[1], 
                             __version__[2])
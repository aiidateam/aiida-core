import pickle, subprocess

def run_command(host, command):
    # need passwordless ssh logins between cluster and server
    '''simple shortcut for system calls'''
    if 'localhost' in host:
        subprocess.call(command, shell=True)
    else:
        #do remote command
        command = 'ssh %s ' % (host) + command
        subprocess.call(command, shell=True)

def write_pickle(filename, object):
    '''general pickle shortcut'''
    f = open(filename, 'wb')
    pickle.dump(object, f)
    f.close()

def read_pickle(filename):
    '''general pickle shortcut'''
    f = open(filename, 'rb')
    object = pickle.load(f)
    f.close()
    return object

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)
        

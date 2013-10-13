from xmlrpclib import ServerProxy, Error
from .io import dirty_qe
# server = ServerProxy("http://localhost:8000") # local server
moka_server = ServerProxy("http://localhost:8088")

def view(s):
    
    try:
        data = dirty_qe(s)
        moka_server.RpcOpener.importQeInput(data)
    except Error as v:
        print "ERROR", v
    

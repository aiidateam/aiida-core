from xmlrpclib import ServerProxy, Error
from .io import dirty_qe
# server = ServerProxy("http://localhost:8000") # local server
moka_server = ServerProxy("http://localhost:8088")

start_prefix = "####----start:"
end_prefix  = "####----end:"

def get_structures(lines):

    structs = []
    buff = ""
    
    in_structure = False;
    for line in lines.split("\n"):
        
        if line.startswith(start_prefix):
            in_structure = True;
        
        elif line.startswith(end_prefix):
            if (in_structure):
                structs.append(buff)
            buff=""
            in_structure = False;
        
        else:
            if (in_structure):
                buff+=line+"\n"
    
    return structs

def view(s):
    
    try:
        data = start_prefix+"\n"+dirty_qe(s)+end_prefix
        moka_server.RpcOpener.importQeInput(data)
    except Error as v:
        print "ERROR", v

def get():

    import tempfile
    import ase.io

    try:
        data    = moka_server.RpcOpener.exportInp("Xsf")
        pwin     = get_structures(data)[0]
        
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(pwin)
            temp.flush()
            ase_s = ase.io.read(temp.name, format="xsf")

        return ase_s

    except Error as v:
        print "ERROR", v

def get_many(verbose=False):

    import tempfile
    import ase.io

    try:
        data     = moka_server.RpcOpener.exportAllInp("Xsf")
        if verbose:
            print data
        all_pwin = get_structures(data)
        all_ase  = []
        
        for pwin in all_pwin:
            
            with tempfile.NamedTemporaryFile() as temp:
                temp.write(pwin)
                temp.flush()
                all_ase.append(ase.io.read(temp.name, format="xsf"))

        return all_ase

    except Error as v:
        print "ERROR", v


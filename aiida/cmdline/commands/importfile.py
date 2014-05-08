import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

def import_file(infile):     
    import tarfile

    from aiida.common.folders import SandboxFolder

    import json

    try:
        with tarfile.open(infile, "r:gz") as tar:
            with SandboxFolder() as folder:
                print "UNCOMPRESSING..."
                # TODO: CHECKS ON EXTRACTALL
                tar.extractall(path=folder.abspath,
                               members=tar.getmembers())
               
                # TODO: CHECKS ON WHETHER THE FILE EXISTS
                with open(folder.get_abs_path('metadata.json')) as f:
                    metadata = json.load(f)

                with open(folder.get_abs_path('data.json')) as f:
                    data = json.load(f)
    except tarfile.ReadError:
        raise ValueError("The input file format for import is not valid (1)")
    
    print "DONE."


class Import(VerdiCommand):
    """
    Export nodes and group of nodes

    This command allows to export to file nodes and group of nodes, for backup
    purposes or to share data with collaborators.
    """
    def run(self,*args):                    
        load_django()

        from aiida.djsite.db import models
        
        print "FEATURE UNDER DEVELOPMENT!"

        if len(args) != 1:
            print "Pass a file name to import"
            sys.exit(1)
        

        ## TODO: parse cmdline parameters and pass them
        ## in particular: also_parents; what; outputfile
        import_file(args[0])

    def complete(self,subargs_idx, subargs):
        return ""

# Following code: to serialize the date directly when dumping into JSON.
# In our case, it is better to have a finer control on how to parse fields.

#def default_jsondump(data):
#    import datetime 
#
#    if isinstance(data, datetime.datetime):
#        return data.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
#    
#    raise TypeError(repr(data) + " is not JSON serializable")
#with open('testout.json', 'w') as f:
#    json.dump({
#            'entries': serialized_entries,             
#        },
#        f,
#        default=default_jsondump)

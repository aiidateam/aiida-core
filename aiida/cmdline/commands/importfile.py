import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

def import_file(infile):     
    import json
    import os
    import tarfile

    from aiida.common.folders import SandboxFolder

    
    try:
        with tarfile.open(infile, "r:gz", format=tarfile.PAX_FORMAT) as tar:
            with SandboxFolder() as folder:
                print "READING DATA AND METADATA..."                
                tar.extract(path=folder.abspath,
                       member=tar.getmember('metadata.json'))
                tar.extract(path=folder.abspath,
                       member=tar.getmember('data.json'))
                
                # TODO: CHECKS ON WHETHER THE FILE EXISTS
                with open(folder.get_abs_path('metadata.json')) as f:
                    metadata = json.load(f)

                with open(folder.get_abs_path('data.json')) as f:
                    data = json.load(f)

                print "EXTRACTING NODE DATA..."
                for member in tar.getmembers():
                    if member.isdev():
                        # safety: skip if character device, block device or FIFO
                        print >> sys.stderr, ("WARNING, device found inside the "
                            "import file: {}".format(member.name))
                        continue
                    if member.issym() or member.islnk():
                        # safety: in export, I set dereference=True therefore
                        # there should be no symbolic or hard links.
                        print >> sys.stderr, ("WARNING, link found inside the "
                            "import file: {}".format(member.name))
                        continue
                    if not member.name.startswith('nodes'+os.sep):
                        continue
                    tar.extract(path=folder.abspath,
                                member=member)
                print os.listdir(folder.abspath)
                print os.listdir(folder.abspath + "/nodes")
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

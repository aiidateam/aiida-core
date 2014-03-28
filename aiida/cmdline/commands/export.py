import sys

from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django

class Export(VerdiCommand):
    """
    Export nodes and group of nodes

    This command allows to export to file nodes and group of nodes, for backup
    purposes or to share data with collaborators.
    """
    def run(self,*args):               
        from aiida.common.folders import SandboxFolder
        from aiida.orm import Node

        import tarfile
        
        load_django()

        print >> sys.stderr, "WARNING! TEST IMPLEMENTATION."
        
        if len(args) != 2:
            print "PASS PK AND OUTFILENAME!"
            sys.exit(1)
            
        pk = int(args[0])
        outfile = args[1]
        
        node = Node.get_subclass_from_pk(pk)
        
        with SandboxFolder() as folder:
            nodesubfolder = folder.get_subfolder('nodes',create=True,
                                                 reset_limit=True)
            # ToDo: sharding?
            thisnodefolder = nodesubfolder.get_subfolder(node.uuid, create=True,
                                                         reset_limit=True)
            thisnodefolder.insert_path(src=node.path_subfolder.abspath)
        
            with tarfile.open(outfile, "w:gz") as tar:
                tar.add(folder.abspath, arcname="aiida")
                
        print >> sys.stderr, "Not completely implemented yet."

    def complete(self,subargs_idx, subargs):
        return ""

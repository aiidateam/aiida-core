import sys
import os
import subprocess

from aiida.cmdline.baseclass import VerdiCommand


class Workflow(VerdiCommand):
    """
    Manage the AiiDA worflow manager
    
    Valid subcommands are:
    * list: list the workflows running and the status
    """


    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        self.valid_subcommands = {
            'list': self.workflow_list
            }

    def run(self,*args):       
        """
        Run the specified workflow subcommand.
        """
        try:
            function_to_call = self.valid_subcommands.get(
                args[0], self.invalid_subcommand)
        except IndexError:
            function_to_call = self.no_subcommand
            
        function_to_call(*args[1:])

    def complete(self,subargs_idx, subargs):
        """
        Complete the workflow subcommand.
        """
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        else:
            print ""

    def no_subcommand(self):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'workflow'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'workflow'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    
    def workflow_list(self, *args):
        
        from aiida.common.utils import load_django
        load_django()
        
        
        extended   = False
        expired    = False
        
        if "--ext" in args:
            extended   = True
        
        if "--expired" in args:
            expired   = True
            
        import aiida.orm.workflow as wfs
        wfs.list_workflows(ext=extended, expired=expired) 

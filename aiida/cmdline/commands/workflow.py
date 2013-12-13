import sys
import os
import subprocess

from aiida.cmdline.baseclass import VerdiCommand


class Workflow(VerdiCommand):
    """
    Manage the AiiDA worflow manager
    
    Valid subcommands are:
    * list: list the running workflows running and their state
    * kill: kill a given workflow
    """


    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        self.valid_subcommands = {
            'list': self.workflow_list,
            'kill': self.workflow_kill,
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
        """
        Return a list of workflows on screen
        """
        from aiida.common.utils import load_django
        load_django()
        
        extended = "--extended" in args
        print_all = "--all" in args
            
        import aiida.orm.workflow as wfs
        print wfs.list_workflows(extended=extended, print_all=print_all) 


    def workflow_kill(self, *args):
        """
        Kill a workflow. 
        
        Pass a list of workflow PKs to kill them.
        If you also pass the -f option, no confirmation will be asked.
        """
        from aiida.common.utils import load_django
        load_django()

        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.workflow import kill_from_pk
        from aiida.common.exceptions import NotExistent
        
        force = False
        wfs = []

        args = list(args)

        while args:
            param = args.pop()
            if param == '-f':
                force = True
            else:
                try:
                    wfs.append(int(param))
                except ValueError: 
                    print >> sys.stderr, (
                        "'{}' is not a valid workflow PK.".format(param))
                    sys.exit(2)
        
        if not wfs:
            print >> sys.stderr, "Pass a list of PKs of workflows to kill."
            print >> sys.stderr, ("You can pass -f if you do not want to see "
                                  "a confirmation message")
            sys.exit(1)
        
        if not force:
            sys.stderr.write("Are you sure to kill {} workflow{}? [Y/N] ".format(
                len(wfs), "" if len(wfs)==1 else "s"))
            if not wait_for_confirmation():
                sys.exit(0)
        
        counter = 0
        for wf_pk in wfs:
            try:
                kill_from_pk(wf_pk)
                counter += 1
            except NotExistent:
                print >> sys.stderr, ("WARNING: workflow {} "
                    "does not exist.".format(wf_pk))
        print >> sys.stderr, "{} workflow{} killed.".format(counter,
            "" if counter==1 else "s")

    
# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands


__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

class Workflow(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA worflow manager
    
    Valid subcommands are:
    * list: list the running workflows running and their state. Pass a -h
    |        option for further help on valid options.
    * kill: kill a given workflow
    * report: show the report of a given workflow
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        self.valid_subcommands = {
            'list': (self.workflow_list, self.complete_none),
            'kill': (self.workflow_kill, self.complete_none),
            'report': (self.print_report, self.complete_none),
            'logshow': (self.print_logshow, self.complete_none),
            }

    
    def workflow_list(self, *args):
        """
        Return a list of workflows on screen
        """
        from aiida import load_dbenv
        load_dbenv()

        from aiida.orm.workflow import get_workflow_info
        from aiida.djsite.db.models import DbWorkflow
        from aiida.common.datastructures import wf_states
        from aiida.djsite.utils import get_automatic_user
        
        from django.db.models import Q
        from django.utils import timezone
        import datetime,argparse
       
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA workflows.')
        parser.add_argument('-s', '--short', help="show shorter output (only subworkflows and steps, no calculations)",
                            action='store_true')
        parser.add_argument('-a', '--all-states', help="show all existing AiiDA workflows, not only running ones",
                            action='store_true')
        parser.add_argument('-p', '--past-days', metavar='N', help="add a filter to show only workflows created in the past N days",
                            action='store', type=int)
        parser.add_argument('pks', type=int, nargs='*',
                            help="a list of workflows to show. If empty, all running workflows are shown. If non-empty, automatically sets --all and ignores the -p option.")
        
        tab_size = 2 # how many spaces to use for indentation of subworkflows
        
        args = list(args)
        parsed_args = parser.parse_args(args)
        
        if parsed_args.pks:
            q_object = Q(pk__in=parsed_args.pks)
        else:
            q_object = Q(user=get_automatic_user())
            if not parsed_args.all_states:
                q_object.add(~Q(state=wf_states.FINISHED), Q.AND)
                q_object.add(~Q(state=wf_states.ERROR), Q.AND)
            if parsed_args.past_days:
                now = timezone.now()
                n_days_ago = now - datetime.timedelta(days=parsed_args.past_days)
                q_object.add(Q(ctime__gte=n_days_ago), Q.AND)
    
        wf_list = DbWorkflow.objects.filter(q_object).order_by('ctime')
        
        for w in wf_list:
            if not w.is_subworkflow():
                print "\n".join(get_workflow_info(w, tab_size=tab_size,
                                                         short=parsed_args.short))

        if not wf_list:
            if parsed_args.all_states:
                retstring = "# No workflows found"
            else:
                retstring = "# No running workflows found"


    def print_report(self, *args):
        """
        Print the report of a workflow.
        """
        from aiida import load_dbenv
        from aiida.common.exceptions import NotExistent
        load_dbenv()

        from aiida.orm.workflow import Workflow
        
        if len(args) != 1:
            print >> sys.stderr, "You have to pass a valid workflow PK as a parameter."
            sys.exit(1)
        
        try:
            pk = int(args[0])
        except ValueError:
            print >> sys.stderr, "You have to pass a valid workflow PK as a parameter."
            sys.exit(1)
        
        try:
            w = Workflow.get_subclass_from_pk(pk)
        except NotExistent:
            print >> sys.stderr, "No workflow with PK={} found.".format(pk)
            sys.exit(1)
        
        print "### WORKFLOW pk: {} ###".format(pk)
        print "\n".join(w.get_report())

    
    def workflow_kill(self, *args):
        """
        Kill a workflow. 
        
        Pass a list of workflow PKs to kill them.
        If you also pass the -f option, no confirmation will be asked.
        """
        from aiida import load_dbenv
        load_dbenv()

        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.workflow import kill_from_pk
        from aiida.common.exceptions import NotExistent
        from aiida.orm.workflow import WorkflowKillError,WorkflowUnkillable
        
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
                kill_from_pk(wf_pk,verbose=True)
                counter += 1
            except NotExistent:
                print >> sys.stderr, ("WARNING: workflow {} "
                    "does not exist.".format(wf_pk))
            except WorkflowKillError as e:
                to_print = ""
                for msg in e.error_message_list:
                    to_print += msg + "\n"
                to_print += "{}: {}\n".format(e.__class__.__name__,e.message)
                sys.stdout.write(to_print)
            except WorkflowUnkillable as e:
                sys.stdout.write("{}: {}\n".format(e.__class__.__name__,
                                                   e.message))
                
        print >> sys.stderr, "{} workflow{} killed.".format(counter,
            "" if counter<=1 else "s")


    def print_logshow(self, *args):
        from aiida.common.exceptions import NotExistent
        from aiida.orm.workflow import Workflow
        from aiida.djsite.utils import get_log_messages
        from aiida.common.datastructures import calc_states
        from aiida import load_dbenv
        
        load_dbenv()
        
        for wf_pk in args:
            try:
                wf = Workflow.get_subclass_from_pk(int(wf_pk))
            except ValueError:
                print "*** {}: Not a valid PK".format(wf_pk)
                continue
            except NotExistent:
                print "*** {}: Not a valid Workflow".format(wf_pk)
                continue

            log_messages = get_log_messages(wf)
            label_string = " [{}]".format(wf.label) if wf.label else ""
            state = wf.get_status()
            print "*** {}{}: {}".format(wf_pk, label_string, state)

            if wf.get_report():
                print "Print the report with 'verdi workflow report {}'".format(wf_pk)
            else:
                print "*** Report is empty"
                            
            if log_messages:
                print "*** {} LOG MESSAGES:".format(len(log_messages))
            else:
                print "*** 0 LOG MESSAGES"
                
            for log in log_messages:
                print "+-> {} at {}".format(log['levelname'], log['time'])
                # Print the message, with a few spaces in front of each line
                print "\n".join(["|   {}".format(_)
                                 for _ in log['message'].splitlines()])

    
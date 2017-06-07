# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands


class Workflow(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA legacy worflow manager

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
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded

        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.backends.utils import get_workflow_list, get_automatic_user
        from aiida.orm.workflow import get_workflow_info
        from aiida.orm import User

        import argparse

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA workflows.')
        parser.add_argument(
            '-s', '--short', action='store_true',
            help="show shorter output "
                 "(only subworkflows and steps, no calculations)")
        parser.add_argument(
            '-a', '--all-states', action='store_true',
            help="show all existing "
                 "AiiDA workflows, not only running ones", )
        parser.add_argument(
            '-d', '--depth', metavar='M', action='store', type=int, default=16,
            help="add a filter "
                 "to show only steps down to a depth of M levels in "
                 "subworkflows (0 means only the parent "
                 "workflows are shown)")
        parser.add_argument(
            '-p', '--past-days', metavar='N', action='store', type=int,
            help="add a "
                 "filter to show only workflows created in the past N days")
        parser.add_argument(
            'pks', type=int, nargs='*',
            help="a list of workflows to show. If empty, "
                 "all running workflows are shown. If non-empty, "
                 "automatically sets --all and ignores the -p option.")

        tab_size = 2  # how many spaces to use for indentation of subworkflows

        args = list(args)
        parsed_args = parser.parse_args(args)

        workflows = get_workflow_list(parsed_args.pks,
                                      user=User(dbuser=get_automatic_user()),
                                      all_states=parsed_args.all_states,
                                      n_days_ago=parsed_args.past_days)

        for w in workflows:
            if not w.is_subworkflow() or w.pk in parsed_args.pks:
                print "\n".join(get_workflow_info(w, tab_size=tab_size,
                                                  short=parsed_args.short,
                                                  depth=parsed_args.depth))
        if not workflows:
            if parsed_args.all_states:
                print "# No workflows found"
            else:
                print "# No running workflows found"

    def print_report(self, *args):
        """
        Print the report of a workflow.
        """
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.utils import load_workflow
        from aiida.common.exceptions import NotExistent

        if len(args) != 1:
            print >> sys.stderr, "You have to pass a valid workflow PK as a parameter."
            sys.exit(1)

        try:
            pk = int(args[0])
        except ValueError:
            print >> sys.stderr, "You have to pass a valid workflow PK as a parameter."
            sys.exit(1)

        try:
            w = load_workflow(pk)
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
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.cmdline import wait_for_confirmation
        from aiida.orm.workflow import kill_from_pk
        from aiida.common.exceptions import NotExistent
        from aiida.orm.workflow import WorkflowKillError, WorkflowUnkillable

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
            sys.stderr.write(
                "Are you sure to kill {} workflow{}? [Y/N] ".format(
                    len(wfs), "" if len(wfs) == 1 else "s"))
            if not wait_for_confirmation():
                sys.exit(0)

        counter = 0
        for wf_pk in wfs:
            try:
                kill_from_pk(wf_pk, verbose=True)
                counter += 1
            except NotExistent:
                print >> sys.stderr, ("WARNING: workflow {} "
                                      "does not exist.".format(wf_pk))
            except WorkflowKillError as e:
                to_print = ""
                for msg in e.error_message_list:
                    to_print += msg + "\n"
                to_print += "{}: {}\n".format(e.__class__.__name__, e.message)
                sys.stdout.write(to_print)
            except WorkflowUnkillable as e:
                sys.stdout.write("{}: {}\n".format(e.__class__.__name__,
                                                   e.message))

        print >> sys.stderr, "{} workflow{} killed.".format(counter,
                                                            "" if counter <= 1 else "s")

    def print_logshow(self, *args):
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.utils import load_workflow
        from aiida.backends.utils import get_log_messages
        from aiida.common.exceptions import NotExistent

        for wf_pk in args:
            try:
                wf = load_workflow(int(wf_pk))
            except ValueError:
                print "*** {}: Not a valid PK".format(wf_pk)
                continue
            except NotExistent:
                print "*** {}: Not a valid Workflow".format(wf_pk)
                continue

            log_messages = get_log_messages(wf)
            label_string = " [{}]".format(wf.label) if wf.label else ""
            state = wf.get_state()
            print "*** {}{}: {}".format(wf_pk, label_string, state)

            if wf.get_report():
                print "Print the report with 'verdi workflow report {}'".format(
                    wf_pk)
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

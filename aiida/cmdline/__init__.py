# -*- coding: utf-8 -*-
# default execname; can be substituted later in the call from
# exec_from_cmdline

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

execname = 'verdi'

def wait_for_confirmation(valid_positive=["Y", "y"], valid_negative=["N", "n"],
        print_to_stderr=True, catch_ctrl_c=True):
    """
    Wait for confirmation, until a valid confirmation is given. If the
    confirmation is not valid, keep asking.
    
    :param valid_positive: a list of strings with all possible valid
        positive confirmations.
    :param valid_negative: a list of strings with all possible valid
        negative confirmations.        
    :param print_to_stderr: If True, print messages to stderr, otherwise
        to stdout
    :param catch_ctrl_c: If True, a CTRL+C command is catched and interpreted
        as a negative response. If False, CTRL+C is not catched.
    
    :returns: True if the reply fas positive, False if it was negative.
    """
    import sys
    
    try:
        while True:
            reply = raw_input()
            if reply in valid_positive:
                return True
            elif reply in valid_negative:
                return False
            else:
                error_string = "The choice is not valid. Valid choices are: {}".format(
                   ", ".join(sorted(list(set(_.upper() for _ in (
                      valid_positive + valid_negative))))))
                if print_to_stderr:
                    outfile = sys.stderr
                else:
                    outfile = sys.stdout
                    
                outfile.write(error_string)
                outfile.write('\n')
                outfile.write("Enter your choice: ")

    except KeyboardInterrupt:
        if catch_ctrl_c:
            return False
        else:
            raise
          
def pass_to_django_manage(argv):
    """
    Call the corresponding django manage.py command
    """
    from aiida.common.utils import load_django
    import django.core.management
    
    load_django()
    django.core.management.execute_from_command_line(argv)
      
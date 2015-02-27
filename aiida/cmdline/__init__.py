# -*- coding: utf-8 -*-
# default execname; can be substituted later in the call from
# exec_from_cmdline

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"

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
    
    :returns: True if the reply was positive, False if it was negative.
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

def _print_dictionary_json_date(dictionary):
    """
    Print a dictionary using the json format (with indent=2),
    and converting dates to strings.
    """
    def default_jsondump(data):
        """
        Function needed to decode datetimes, that would otherwise
        not be JSON-decodable
        """
        import datetime 

        if isinstance(data, datetime.datetime):
            return data.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        
        raise TypeError(repr(data) + " is not JSON serializable")

    import json
    print json.dumps(dictionary, indent=2, sort_keys = True,
                     default=default_jsondump)


def print_dictionary(dictionary, format):
    import sys
    valid_formats_table = {'json+date': _print_dictionary_json_date}
    
    try:
        actual_printing_function = valid_formats_table[format]
    except KeyError:
        print >> sys.stderr, ("Unrecognised printing format. Valid formats "
            "are: {}".format(",".join(valid_formats_table.keys())))
        sys.exit(1)

    actual_printing_function(dictionary)
    
          
def pass_to_django_manage(argv,profile=None):
    """
    Call the corresponding django manage.py command
    """
    from aiida import load_dbenv
    import django.core.management
    
    load_dbenv(profile=profile)
    django.core.management.execute_from_command_line(argv)
      
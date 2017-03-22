# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# default execname; can be substituted later in the call from
# exec_from_cmdline


execname = 'verdi'


def delayed_load_node(*args, **kwargs):
    """
    Call the aiida.orm.load_node, but import the module only at the
    first execution. This is needed in the command line, because an
    import would "freeze" the imported modules to the BACKEND currently
    set (and when 'verdi' starts to run, this has not been fixed yet).

    :note: either import load_node AFTER the load_dbenv call, inside each
      function, or if you want to import it only once for convenience reasons,
      import this function::

        from aiida.cmdline import delayed_load_node as load_node
    """
    from aiida.orm.utils import load_node as orig_load_node
    return orig_load_node(*args, **kwargs)


def delayed_load_workflow(*args, **kwargs):
    """
    Same as aiida.cmdline.delayed_load_node. This method is needed in the
    command line in order not to "freeze" what is imported to a specific
    backend.
    """
    from aiida.orm.utils import load_workflow as orig_load_workflow
    return orig_load_workflow(*args, **kwargs)


def wait_for_confirmation(valid_positive=("Y", "y"), valid_negative=("N", "n"),
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

    print json.dumps(dictionary, indent=2, sort_keys=True,
                     default=default_jsondump)


def print_dictionary(dictionary, format):
    import sys

    valid_formats_table = {'json+date': _print_dictionary_json_date}

    try:
        actual_printing_function = valid_formats_table[format]
    except KeyError:
        print >> sys.stderr, ("Unrecognised printing format. Valid formats "
                              "are: {}".format(
            ",".join(valid_formats_table.keys())))
        sys.exit(1)

    actual_printing_function(dictionary)


def pass_to_django_manage(argv, profile=None):
    """
    Call the corresponding django manage.py command
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv(profile=profile)

    import django.core.management
    django.core.management.execute_from_command_line(argv)

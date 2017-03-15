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
import os

import aiida
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline import pass_to_django_manage, execname
from aiida.common.exceptions import InternalError, TestsNotAllowedError



def applyfunct_len(value):
    """
    Return the length of an object.
    """
    try:
        return len(value)
    except Exception as e:
        raise InternalError(e, 'Error in function len, probably the object has no "len"?')


def applyfunct_keys(value):
    """
    Return the keys of a dictionary.
    """
    try:
        return value.keys()
    except Exception as e:
        raise InternalError(e, 'Error in function keys, probably not a dict?')


def apply_function(function, value):
    """
    The function must be defined in this file and be in the format
    applyfunct_FUNCNAME
    where FUNCNAME is the string passed as the parameter 'function';
    applyfunct_FUNCNAME will accept only one parameter ('value') and
    return an appropriate value.
    """
    function_prefix = "applyfunct_"
    if function is None:
        return value
    else:
        try:
            return globals()[function_prefix + function](value)
        except KeyError as e:
            # Raising an InternalError means that a default value is printed
            # if no function exists.
            # Instead, raising a ValueError will always get printed even if
            # a default value is printed, that is what one wants
            # raise InternalError(
            #                real_exception=e, message =
            raise ValueError(
                "o such function %s. Available functions are: %s." %
                (function,
                 ", ".join(i[len(function_prefix):] for i in globals() if i.startswith(function_prefix))))


class Devel(VerdiCommandWithSubcommands):
    """
    AiiDA commands for developers

    Provides a set of tools for developers. For instance, it allows to run
    the django tests for the db application and the unittests of
    the AiiDA modules.

    If you want to limit the tests to a specific subset of modules,
    pass them as parameters.

    An invalid parameter will make the code print the list of all
    valid parameters.

    Note: the test called 'db' will run all db.* tests.
    """
    base_allowed_test_folders = [
        'aiida.scheduler',
        'aiida.transport',
        'aiida.common',
        'aiida.tests.work',
        'aiida.utils'
    ]

    _dbrawprefix = "db"
    _dbprefix = _dbrawprefix + "."

    def __init__(self, *args, **kwargs):
        from aiida.backends.tests import get_db_test_names
        from aiida.backends import settings

        db_test_list = get_db_test_names()

        super(Devel, self).__init__(*args, **kwargs)

        self.valid_subcommands = {
            'tests': (self.run_tests, self.complete_tests),
            'query': (self.run_query, self.complete_none),  # For the moment, no completion
            'setproperty': (self.run_setproperty, self.complete_properties),
            'getproperty': (self.run_getproperty, self.complete_properties),
            'delproperty': (self.run_delproperty, self.complete_properties),
            'describeproperties': (self.run_describeproperties, self.complete_none),
            'listproperties': (self.run_listproperties, self.complete_none),
            'listislands': (self.run_listislands, self.complete_none),
            'play': (self.run_play, self.complete_none),
            'getresults': (self.calculation_getresults, self.complete_none),
            'tickd': (self.tick_daemon, self.complete_none)
        }

        # The content of the dict is:
        # None for a simple folder test
        #   a list of strings for db tests, one for each test to run
        self.allowed_test_folders = {}
        for k in self.base_allowed_test_folders:
            self.allowed_test_folders[k] = None

        for dbtest in db_test_list:
            self.allowed_test_folders["{}{}".format(self._dbprefix, dbtest)] = [dbtest]
        self.allowed_test_folders[self._dbrawprefix] = db_test_list

    def complete_properties(self, subargs_idx, subargs):
        """
        I complete with subargs that were not used yet.
        """
        from aiida.common.setup import _property_table

        if subargs_idx == 0:
            return " ".join(_property_table.keys())
        else:
            return ""

    def run_describeproperties(self, *args):
        """
        List all valid properties that can be stored in the AiiDA config file.

        Only properties listed in the ``_property_table`` of
        ``aida.common.setup`` can be used.
        """
        from aiida.common.setup import _property_table, _NoDefaultValue

        if args:
            print >> sys.stderr, ("No parameters allowed for {}".format(
                self.get_full_command_name()))
            sys.exit(1)

        for prop in sorted(_property_table.keys()):
            if _property_table[prop][4] is None:
                valid_vals_str = ""
            else:
                valid_vals_str = " Valid values: {}.".format(",".join(
                    str(_) for _ in _property_table[prop][4]))
            if isinstance(_property_table[prop][3], _NoDefaultValue):
                def_val_string = ""
            else:
                def_val_string = " (default: {})".format(
                    _property_table[prop][3])
            print "* {} ({}): {}{}{}".format(prop, _property_table[prop][1],
                                             _property_table[prop][2],
                                             def_val_string, valid_vals_str)

    def calculation_getresults(self, *args):
        """
        Routine to get a list of results of a set of calculations, still
        under development.
        """
        from aiida.common.exceptions import AiidaException
        load_dbenv()
        from aiida.orm import JobCalculation as OrmCalculation
        from aiida.orm.utils import load_node


        class InternalError(AiidaException):
            def __init__(self, real_exception, message):
                self.real_exception = real_exception
                self.message = message


        def get_suggestions(key, correct_keys):
            import difflib
            import string

            similar_kws = difflib.get_close_matches(key, correct_keys)
            if len(similar_kws) == 1:
                return "(Maybe you wanted to specify %s?)" % similar_kws[0]
            elif len(similar_kws) > 1:
                return "(Maybe you wanted to specify one of these: %s?)" % string.join(similar_kws, ', ')
            else:
                return "(No similar keywords found...)"

        # define a function to retrieve the data from the dictionary
        def key_finder(in_dict, the_keys):
            parent_dict = in_dict
            parent_dict_name = '<root level>'
            for new_key in the_keys:
                try:
                    parent_dict = parent_dict[new_key]
                    parent_dict_name = new_key
                except KeyError as e:
                    raise InternalError(e, "Unable to find the key '%s' in '%s' %s" % (
                        new_key, parent_dict_name, get_suggestions(new_key, parent_dict.keys())))
                except Exception as e:
                    if e.__class__ is not InternalError:
                        raise InternalError(e,
                                            "Error retrieving the key '%s' withing '%s', maybe '%s' is not a dict?" % (
                                                the_keys[1], the_keys[0], the_keys[0]))
                    else:
                        raise
            return parent_dict


        def index_finder(data, indices, list_name):
            if not indices:
                return data

            parent_data = data
            parent_name = list_name
            for idx in indices:
                try:
                    index = int(idx)
                    parent_data = parent_data[index]
                    parent_name += ":%s" % index
                except ValueError as e:
                    raise InternalError(e, "%s is not a valid integer (in %s)." % (idx, parent_name))
                except IndexError as e:
                    raise InternalError(e, "Index %s is out of bounds, length of list %s is %s" % (
                        index, parent_name, len(parent_data)))
                except Exception as e:
                    raise InternalError(e, "Invalid index! Maybe %s is not a list?" % parent_name)
            return parent_data


        if not args:
            print >> sys.stderr, "Pass some parameters."
            sys.exit(1)

        # I convert it to a list
        arguments = list(args)

        try:
            sep_idx = arguments.index('--')
        except ValueError:
            print >> sys.stderr, "Separate parameter keys from job-ids with a --!"
            sys.exit(1)

        keys_to_retrieve = arguments[:sep_idx]
        job_list_str = arguments[sep_idx + 1:]

        try:
            job_list = [int(i) for i in job_list_str]
        except ValueError:
            print >> sys.stderr, "All PKs after -- must be valid integers."
            sys.exit(1)


        sep = '\t'  # Default separator: a tab character

        try:
            idx = keys_to_retrieve.index('-s')

            # First pop removes the -s parameter, second pop (now with the same
            # index) retrieves the asked separator. Raises IndexError if nothing
            # is provided after -s.
            _ = keys_to_retrieve.pop(idx)
            sep = keys_to_retrieve.pop(idx)
        except IndexError:
            print >> sys.stderr, "After -s you have to pass a valid separator!"
            sys.exit(1)
        except ValueError:
            # No -s found, use default separator
            pass

        print_header = True  # Default: print the header
        try:
            keys_to_retrieve.remove('--no-header')
            # If here, the key was found: I remove it from the list and set the
            # the print_header flag
            print_header = False
        except ValueError:
            # No --no-header found: pass
            pass

        # check if there is at least one thing to do
        if not job_list:
            print >> sys.stderr, "Failed recognizing a calculation PK."
            sys.exit(1)
        if not keys_to_retrieve:
            print  >> sys.stderr, "Failed recognizing a key to parse."
            sys.exit(1)

        # load the data
        if print_header:
            print "## Job list: %s" % " ".join(job_list_str)
            print "#" + sep.join(str(i) for i in keys_to_retrieve)
        for job in job_list:
            values_to_print = []
            in_found = True
            out_found = True
            c = load_node(job, parent_class=OrmCalculation)
            try:
                i = c.inp.parameters.get_dict()
            except AttributeError:
                i = {}
                in_found = False
            try:
                o = c.out.output_parameters.get_dict()
            except AttributeError:
                out_found = False
                o = {}

            io = {'extras': c.get_extras(), 'attrs': c.get_attrs(),
                  'i': i, 'o': o, 'pk': job, 'label': c.label,
                  'desc': c.description, 'state': c.get_state(),
                  'sched_state': c.get_scheduler_state(),
                  'owner': c.dbnode.user.email}

            try:
                for datakey_full in keys_to_retrieve:
                    split_for_def = datakey_full.split('=')
                    datakey_raw = split_for_def[0]  # Still can contain the function to apply
                    def_val = "=".join(split_for_def[1:]) if len(split_for_def) > 1 else None

                    split_for_func = datakey_raw.split('/')
                    datakey = split_for_func[0]
                    function_to_apply = "/".join(split_for_func[1:]) if len(split_for_func) > 1 else None

                    key_values = [str(i) for i in datakey.split(':')[0].split('.')]
                    indices = [int(i) for i in datakey.split(':')[1:]]  # empty list for simple variables.
                    try:
                        value_key = key_finder(io, key_values)
                        value = index_finder(value_key, indices, list_name=datakey.split(':')[0])
                        # Will do the correct thing if no function is supplied
                        # and function is therefore None
                        value = apply_function(function=function_to_apply, value=value)

                    except InternalError as e:
                        # For any internal error, set the value to the default if
                        # provided, otherwise re-raise the exception
                        if def_val is not None:
                            value = def_val
                        else:
                            if not out_found:
                                if in_found:
                                    e.message += " [NOTE: No output JSON could be found]"
                                else:
                                    e.message += " [NOTE: No output JSON nor input JSON could be found]"
                            raise e

                    values_to_print.append(value)

                    # Not needed: now we can ask explicitly for a job number using the flag
                    # 'jobnum'
                    # values_to_print.append("# %s" % str(job))
                # print on screen
                print sep.join(str(i) for i in values_to_print)
            except InternalError as e:
                print >> sys.stderr, e.message
            except Exception as e:
                print >> sys.stderr, "# Error loading job # %s (%s): %s" % (job, type(e), e)

    def tick_daemon(self, *args):
        """
        Call all the functions that the daemon would call if running once and
        return.
        """
        from aiida.daemon.tasks import manual_tick_all
        manual_tick_all()

    def run_listproperties(self, *args):
        """
        List all found global AiiDA properties.
        """
        import argparse

        from aiida.common.setup import (
            _property_table, exists_property, get_property)

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List all custom properties stored in the user configuration file.')
        parser.add_argument('-a', '--all',
                            dest='all', action='store_true',
                            help="Show all properties, even if not explicitly defined, if they "
                                 "have a default value.")
        parser.set_defaults(all=False)
        parsed_args = parser.parse_args(args)

        show_all = parsed_args.all

        for prop in sorted(_property_table.keys()):
            try:
                # To enforce the generation of an exception, even if
                # there is a default value
                if show_all or exists_property(prop):
                    val = get_property(prop)
                    print "{} = {}".format(prop, val)
            except KeyError:
                pass

    def run_listislands(self, *args):
        """
        List all AiiDA nodes, that have no parents and children.
        """
        load_dbenv()
        from django.db.models import Q
        from aiida.orm.node import Node
        from aiida.backends.utils import get_automatic_user

        q_object = Q(user=get_automatic_user())
        q_object.add(Q(parents__isnull=True), Q.AND)
        q_object.add(Q(children__isnull=True), Q.AND)

        node_list = Node.query(q_object).distinct().order_by('ctime')
        print "ID\tclass"
        for node in node_list:
            print "{}\t{}".format(node.pk, node.__class__.__name__)

    def run_getproperty(self, *args):
        """
        Get a global AiiDA property from the config file in .aiida.
        """
        from aiida.common.setup import get_property

        if len(args) != 1:
            print >> sys.stderr, ("usage: {} PROPERTYNAME".format(
                self.get_full_command_name()))
            sys.exit()

        try:
            value = get_property(args[0])
        except Exception as e:
            print >> sys.stderr, ("{} while getting the "
                                  "property: {}".format(type(e).__name__, e.message))
            sys.exit(1)
        print "{}".format(value)

    def run_delproperty(self, *args):
        """
        Delete a global AiiDA property from the config file in .aiida.
        """
        from aiida.common.setup import del_property

        if len(args) != 1:
            print >> sys.stderr, ("usage: {} PROPERTYNAME".format(
                self.get_full_command_name()))
            sys.exit()

        try:
            del_property(args[0])
        except KeyError:
            print >> sys.stderr, ("No such property '{}' in the config "
                                  "file.".format(args[0]))
            sys.exit(1)

        except Exception as e:
            print >> sys.stderr, ("{} while getting the "
                                  "property: {}".format(type(e).__name__, e.message))
            sys.exit(1)

        print "Property '{}' successfully deleted.".format(args[0])

    def run_setproperty(self, *args):
        """
        Define a global AiiDA property in the config file in .aiida.

        Only properties in the _property_table of aiida.common.setup can
        be modified.
        """
        from aiida.common.setup import set_property

        if len(args) != 2:
            print >> sys.stderr, ("usage: {} PROPERTYNAME PROPERTYVALUE".format(
                self.get_full_command_name()))
            sys.exit()

        try:
            set_property(args[0], args[1])
        except Exception as e:
            print >> sys.stderr, ("{} while storing the "
                                  "property: {}".format(type(e).__name__, e.message))
            sys.exit(1)

    def run_tests(self, *args):
        import unittest
        from aiida.backends import settings
        from aiida.backends.testbase import run_aiida_db_tests
        from aiida.backends.testbase import check_if_tests_can_run

        # For final summary
        test_failures = []
        test_errors = []
        test_skipped = []
        tot_num_tests = 0

        db_test_list = []
        test_folders = []
        do_db = False
        if args:
            for arg in args:
                if arg in self.allowed_test_folders:
                    dbtests = self.allowed_test_folders[arg]
                    # Anything that has been added is a DB test
                    if dbtests is not None:
                        do_db = True
                        for dbtest in dbtests:
                            db_test_list.append(dbtest)
                    else:
                        test_folders.append(arg)
                else:
                    print >> sys.stderr, (
                        "{} is not a valid test. "
                        "Allowed test folders are:".format(arg))
                    print >> sys.stderr, "\n".join(
                        '  * {}'.format(a) for a in sorted(
                            self.allowed_test_folders.keys()))
                    sys.exit(1)
        else:
            # Without arguments, run all tests
            do_db = True
            for k, v in self.allowed_test_folders.iteritems():
                if v is None:
                    # Non-db tests
                    test_folders.append(k)
                else:
                    # DB test
                    for dbtest in v:
                        db_test_list.append(dbtest)

        for test_folder in test_folders:
            print "v" * 75
            print ">>> Tests for module {} <<<".format(test_folder.ljust(50))
            print "^" * 75
            testsuite = unittest.defaultTestLoader.discover(
                test_folder, top_level_dir=os.path.dirname(aiida.__file__))
            test_runner = unittest.TextTestRunner()
            test_results = test_runner.run(testsuite)
            test_failures.extend(test_results.failures)
            test_errors.extend(test_results.errors)
            test_skipped.extend(test_results.skipped)
            tot_num_tests += test_results.testsRun

        if do_db:
            if not is_dbenv_loaded():
                load_dbenv()

            # Even if each test would fail if we are not in a test profile,
            # it's still better to not even run them in the case the profile
            # is not a test one.
            try:
                check_if_tests_can_run()
            except TestsNotAllowedError as e:
                print >> sys.stderr, e.message
                sys.exit(1)

            # project_dir = os.path.join(os.path.dirname(aiida.__file__), '..')
            # testsuite = unittest.defaultTestLoader.discover('test', top_level_dir=project_dir)
            # test_runner = unittest.TextTestRunner()
            # test_runner.run(testsuite)

            print "v" * 75
            print (">>> Tests for {} db application".format(settings.BACKEND))
            print "^" * 75
            db_results = run_aiida_db_tests(db_test_list)
            test_skipped.extend(db_results.skipped)
            test_failures.extend(db_results.failures)
            test_errors.extend(db_results.errors)
            tot_num_tests += db_results.testsRun

        print "Final summary of the run of tests:"
        print "* Tests skipped: {}".format(len(test_skipped))
        if test_skipped:
            print "  Reasons for skipping:"
            for reason in sorted(set([_[1] for _ in test_skipped])):
                print "  - {}".format(reason)

        print "* Tests run:     {}".format(tot_num_tests)
        # This count is wrong, sometimes a test can both error and fail 
        # apparently, and you can get negative numbers...
        #print "* Tests OK:      {}".format(tot_num_tests - len(test_errors) - len(test_failures))
        print "* Tests failed:  {}".format(len(test_failures))
        print "* Tests errored: {}".format(len(test_errors))



        # If there was any failure report it with the
        # right exit code
        if test_failures or test_errors:
            sys.exit(len(test_failures) + len(test_errors))

    def complete_tests(self, subargs_idx, subargs):
        """
        I complete with subargs that were not used yet.
        """
        # I remove the one on which I am, so if I wrote all of it but
        # did not press space, it will get completed
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx + 1:]
        # I create a list of the tests that are not already written on the
        # command line
        remaining_tests = (
            set(self.allowed_test_folders) - set(other_subargs))

        return " ".join(sorted(remaining_tests))


    def get_querydict_from_keyvalue(self, key, separator_filter, value):
        from aiida.orm import (Code, Data, Calculation,
                               DataFactory, CalculationFactory)
        from aiida.common.exceptions import MissingPluginError
        import re

        item, sep, subproperty = key.partition('.')

        the_type, realvalue = re.match("^(\([^\)]+\))?(.*)$", value).groups()
        value = realvalue

        if the_type is None:
            # default: string
            the_type = "(t)"

        if the_type == '(t)':
            cast_value = value
            attr_field = "tval"
        elif the_type == '(i)':
            cast_value = int(value)
            attr_field = "ival"
        elif the_type == '(f)':
            cast_value = float(value)
            attr_field = "fval"
        else:
            raise ValueError("For the moment only (t), (i) and (f) fields accepted. Got '{}' instead".format(the_type))

        do_recursive = False

        if separator_filter:
            sep_filter_string = "__{}".format(separator_filter)
        else:
            sep_filter_string = ""

        if item == 'i':  # input
            keystring = "inputs"
            do_recursive = True
        elif item == 'o':  # input
            keystring = "outputs"
            do_recursive = True
        elif item == 'p':  # input
            keystring = "parents"
            do_recursive = True
        elif item == 'c':  # input
            keystring = "children"
            do_recursive = True
        elif item == 'a':  # input
            keystring = "dbattributes"
            if '*' in subproperty:
                if sep_filter_string:
                    raise ValueError("Only = allowed if * patterns in the attributes are used")
                regex_key = re.escape(subproperty)
                # I look for non-separators, i.e. the * only covers
                # at a single level, and does not go deeper in levels
                regex_key = regex_key.replace(r'\*', r'[^\.]+')
                # Match the full string
                return ({keystring + "__key__regex": r'^{}$'.format(regex_key),
                         keystring + "__{}".format(attr_field): cast_value},
                        [keystring + "__key", keystring +
                         "__{}".format(attr_field)]
                )
            else:
                # Standard query
                return ({keystring + "__key": subproperty,
                         keystring + "__{}".format(attr_field)
                         + sep_filter_string: cast_value},
                        [keystring + "__key", keystring
                         + "__{}".format(attr_field)]
                )

        elif item == 'e':  # input
            keystring = "dbextras"

            if '*' in subproperty:
                import re

                if sep_filter_string:
                    raise ValueError("Only = allowed if * patterns in the extras are used")
                regex_key = re.escape(subproperty)
                # I look for non-separators, i.e. the * only covers
                # at a single level, and does not go deeper in levels
                regex_key = regex_key.replace(r'\*', r'[^\.]+')
                return ({keystring + "__key__regex": r'^{}$'.format(regex_key),
                         keystring + "__ival": value},
                        [keystring + "__key", keystring + "__ival"],
                )

            else:
                # Standard query
                return ({keystring + "__key": subproperty,
                         keystring + "__ival" + sep_filter_string: value},
                        [keystring + "__key", keystring + "__ival"]
                )


        elif item == 't' or item == 'type':
            if sep_filter_string:
                raise ValueError("Only = allowed for type")
            if subproperty:
                raise ValueError("Cannot pass subproperties to type")

            if value == 'code':
                DataClass = Code
            elif value == 'node':
                return ({}, [])
            elif value == 'calc' or value == 'calculation':
                DataClass = Calculation
            elif value == 'data':
                DataClass = Data
            else:
                try:
                    DataClass = DataFactory(value)
                except MissingPluginError:
                    try:
                        DataClass = CalculationFactory(value)
                    except MissingPluginError:
                        raise ValueError("Unknown node type '{}'".format(value))

            # Startswith so to get also subclasses
            return ({"type__startswith": DataClass._query_type_string},
                    ["type"])

        else:
            # this is a 'direct' attribute: just create the query
            return ({key + sep_filter_string: value},  # all, including the dots
                    [key])

        if do_recursive:
            if sep:
                tempdict, templist = self.get_querydict_from_keyvalue(
                    subproperty,
                    separator_filter,
                    value)
                # In this case the filter is added by the recursive function
                return ({"{}__{}".format(keystring, k): v
                         for k, v in tempdict.iteritems()},
                        ["{}__{}".format(keystring, k) for k in templist] +
                        ["{}__pk".format(keystring),
                         "{}__type".format(keystring),
                         "{}__label".format(keystring)],
                )
            else:
                return ({keystring + sep_filter_string: value},
                        [keystring] +
                        ["{}__pk".format(keystring),
                         "{}__type".format(keystring),
                         "{}__label".format(keystring)],
                )

        raise NotImplementedError("Should not be here...")


    # To be put in the right order! For instance,
    # You want to put ~= before =, because this has
    # to be checked first
    # First element of each tuple: string used as separator
    # Second element of each tuple: django filter to apply
    separators = [
        ("~=", "iexact"),
        (">=", "gte"),
        ("<=", "lte"),
        (">", "gt"),
        ("<", "lt"),
        ("=", ""),
    ]
    # TO ADD: startswith, istartswith, endswith, iendswith, ymdHMS, isnull, in, contains,

    # TO ADD: support for other types


    def parse_arg(self, arg):
        # pieces = arg.split("=")
        #        if len(pieces) != 2:
        #            raise ValueError("Each option must be in the key=value format")
        #        key = pieces[0]
        #        value = pieces[1]

        #import re
        #sep_regex = "|".join([re.escape(k) for k in self.separators.keys()])
        #regex = re.match(r'(.+)(' + sep_regex + r')(.+)',arg)
        #        key, sep, value = regex.groups()

        for s, django_filter in self.separators:
            key, sep, value = arg.partition(s)
            if sep:
                filter_to_apply = django_filter
                break
        if not sep:
            raise ValueError("No separator provided!")

        querydict = self.get_querydict_from_keyvalue(key,
                                                     filter_to_apply,
                                                     value)

        return querydict


    def run_query(self, *args):
        load_dbenv()
        from django.db.models import Q
        from aiida.backends.djsite.db.models import DbNode

        # django_query = Q()
        django_query = DbNode.objects.filter()

        try:
            # NOT SURE THIS IS THE RIGHT WAY OF MANAGING NEGATION FOR
            # ATTRIBUTES!!
            queries = [(self.parse_arg(arg[1:] if arg.startswith('!') else arg), arg.startswith('!')) for arg in args]
        except ValueError as e:
            print "ERROR in format!"
            print e.message
            sys.exit(1)

        all_values = ['pk']

        print "*** DEBUG: QUERY ***" + "*" * 52
        for (q, v), n in queries:
            print "* {}{}".format("[NEG]" if n else "", q)
        print "*" * 72

        for (query, values), negate in queries:

            all_values += list(values)
            if negate:
                if len(query) == 1:
                    #                    django_query = django_query & ~Q(**query)
                    django_query = django_query.filter(~Q(**query))
                elif len(query) == 2:

                    raise NotImplementedError(
                        "The current implementation does not work for negation of attributes. See comments in source code.")

                    ## NOT THE RIGHT WAY TO MANAGE NEGATIONS!! SEE AT THE
                    ## END OF THE FILE
                    temp = [(k, v) for k, v in query.iteritems()]
                    if temp[0][0].endswith("__key"):
                        #                        django_query = django_query & (
                        #                            Q(~Q(**{temp[1][0]: temp[1][1]}),
                        #                               **{temp[0][0]: temp[0][1]})
                        django_query = django_query.filter(~Q(**{temp[1][0]: temp[1][1]}),
                                                           **{temp[0][0]: temp[0][1]})
                    elif temp[1][0].endswith("__key"):
                        django_query = django_query.filter(~Q(**{temp[0][0]: temp[0][1]}),
                                                           **{temp[1][0]: temp[1][1]})
                    else:
                        raise NotImplementedError("Should not be here... no key search?")
                else:
                    raise NotImplementedError("Should not be here...")
            else:
                django_query = django_query.filter(Q(**query))

        res = django_query.distinct().order_by('pk')
        res = res.values_list(*all_values)
        print res.query
        print "{} matching nodes found ({} removing duplicates).".format(len(res),
                                                                         len(set([_[0] for _ in res])))
        #        for node in res:
        #            print "* {}".format(str(node))
        #            print "* {} ({}){}".format(
        #                node.pk, node.get_aiida_class().__class__.__name__,
        #                " [{}]".format(node.label) if node.label else "")
        for node in res:
            print "* {}".format(node[0])
            for p, v in zip(all_values[1:], node[1:]):
                print "  `-> {} = {}".format(p, v)


    def run_play(self, *args):
        """
        Open a browser and play the Aida triumphal march by Giuseppe Verdi
        """
        import webbrowser

        webbrowser.open_new('http://upload.wikimedia.org/wikipedia/commons/3/32/Triumphal_March_from_Aida.ogg')

# In [11]: attr_res = DbAttribute.objects.filter(Q(key='cell.atoms'), ~Q(ival__gt=7))
#
#In [12]: dbres = DbNode.objects.filter(outputs__dbattributes__in=attr_res).distinct()
#
#In [13]: print dbres.query
#SELECT DISTINCT "db_dbnode"."id", "db_dbnode"."uuid", "db_dbnode"."type", "db_dbnode"."label", "db_dbnode"."description", "db_dbnode"."ctime", "db_dbnode"."mtime", "db_dbnode"."user_id", "db_dbnode"."dbcomputer_id", "db_dbnode"."nodeversion", "db_dbnode"."lastsyncedversion" FROM "db_dbnode" INNER JOIN "db_dblink" ON ("db_dbnode"."id" = "db_dblink"."input_id") INNER JOIN "db_dbnode" T3 ON ("db_dblink"."output_id" = T3."id") INNER JOIN "db_dbattribute" ON (T3."id" = "db_dbattribute"."dbnode_id") WHERE "db_dbattribute"."id" IN (SELECT U0."id" FROM "db_dbattribute" U0 WHERE (U0."key" = cell.atoms  AND NOT ((U0."ival" > 7  AND U0."ival" IS NOT NULL))))

## OR, if doing
#dbres = DbNode.objects.filter(dbattributes__in=attr_res).distinct()
#In [18]: print dbres.query
#SELECT DISTINCT "db_dbnode"."id", "db_dbnode"."uuid", "db_dbnode"."type", "db_dbnode"."label", "db_dbnode"."description", "db_dbnode"."ctime", "db_dbnode"."mtime", "db_dbnode"."user_id", "db_dbnode"."dbcomputer_id", "db_dbnode"."nodeversion", "db_dbnode"."lastsyncedversion" FROM "db_dbnode" INNER JOIN "db_dbattribute" ON ("db_dbnode"."id" = "db_dbattribute"."dbnode_id") WHERE "db_dbattribute"."id" IN (SELECT U0."id" FROM "db_dbattribute" U0 WHERE (U0."key" = cell.atoms  AND NOT ((U0."ival" > 7  AND U0."ival" IS NOT NULL))))

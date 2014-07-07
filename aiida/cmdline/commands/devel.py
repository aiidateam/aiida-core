# -*- coding: utf-8 -*-
import sys
import os

import aiida
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.common.utils import load_django
from aiida.cmdline import pass_to_django_manage, execname

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

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
        ]
    
    _dbrawprefix = "db"
    _dbprefix = _dbrawprefix + "."

    def __init__(self,*args,**kwargs):
        from aiida.djsite.db.testbase import db_test_list
        
        super(Devel, self).__init__(*args, **kwargs)

        self.valid_subcommands = {
            'tests': (self.run_tests, self.complete_tests),
            'query': (self.run_query, self.complete_none), # For the moment, no completion
            'setproperty': (self.run_setproperty, self.complete_properties), 
            'getproperty': (self.run_getproperty, self.complete_properties),
            'delproperty': (self.run_delproperty, self.complete_properties),
            'describeproperties': (self.run_describeproperties, self.complete_none),
            'listproperties': (self.run_listproperties, self.complete_none),
            'play': (self.run_play, self.complete_none),
            }
        
        # The content of the dict is:
        #   None for a simple folder test
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
        List all found properties
        """
        from aiida.common.setup import _property_table, _NoDefaultValue
        
        if args:
            print >> sys.stderr, ("No parameters allowed for {}".format(
                self.get_full_command_name()))
            sys.exit(1)
        
        for prop in sorted(_property_table.keys()):
            if isinstance(_property_table[prop][3], _NoDefaultValue):
                def_val_string = ""
            else:
                def_val_string = " (default: {})".format(
                    _property_table[prop][3])
            print "{} ({}): {}{}".format(prop, _property_table[prop][1],
                                       _property_table[prop][2],
                                       def_val_string)
    
    def run_listproperties(self, *args):
        """
        List all found properties
        """
        import argparse
        
        from aiida.common.setup import (
            _property_table, exists_property, get_property)
                
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List all custom properties stored in the user configuration file.')
        parser.add_argument('-a', '--all',
            dest='all',action='store_true',
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

    def run_getproperty(self, *args):
        """
        Get a property from the config file.
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
        Delete a property from the config file.
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
        Define a property in the config file.
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
           
    def run_tests(self,*args):
        import unittest
        import tempfile
        from aiida.djsite.settings import settings
        from aiida.common.setup import get_property

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
            print "v"*75
            print ">>> Tests for module {} <<<".format(test_folder.ljust(50))
            print "^"*75
            testsuite = unittest.defaultTestLoader.discover(
                test_folder,top_level_dir = os.path.dirname(aiida.__file__))
            test_runner = unittest.TextTestRunner()
            test_runner.run( testsuite )

        if do_db:
            # As a first thing, I want to set the correct flags.
            # This allow to work on temporary DBs and a temporary repository.

            ## Setup a sqlite3 DB for tests (WAY faster, since it remains in-memory
            ## and not on disk.
            # if you define such a variable to False, it will use the same backend
            # that you have already configured also for tests. Otherwise, 
            # Setup a sqlite3 DB for tests (WAY faster, since it remains in-memory)

            # TODO: allow the use of this flag
            if get_property('tests.use_sqlite'):
                settings.DATABASES['default'] = {'ENGINE':
                                                 'django.db.backends.sqlite3'}
            ###################################################################
            # IMPORTANT! Choose a different repository location, otherwise 
            # real data will be destroyed during tests!!
            # The location is automatically created with the tempfile module
            # Typically, under linux this is created under /tmp
            # and is not deleted at the end of the run.
            settings.LOCAL_REPOSITORY = tempfile.mkdtemp(prefix='aiida_repository_')
            # I write the local repository on stderr, so that the user running
            # the tests knows where the files are being stored
            print >> sys.stderr, "########################################"
            print >> sys.stderr, "# LOCAL AiiDA REPOSITORY FOR TESTS:"
            print >> sys.stderr, "# {}".format(settings.LOCAL_REPOSITORY)
            print >> sys.stderr, "########################################"
            # Here. I set the correct signal to attach to when we want to
            # perform an operation after all tables are created (e.g., creation
            # of the triggers).
            # By default, in djsite/settings/settings.py this is south->post_migrate,
            # here we set it to django->post_syncdb because we have set
            # SOUTH_TESTS_MIGRATE = False
            # in the settings.
            settings.AFTER_DATABASE_CREATION_SIGNAL = 'post_syncdb'
            
            ##################################################################
            ## Only now I set the aiida_test_list variable so that tests can run
            settings.aiida_test_list = db_test_list
            
            print "v"*75
            print (">>> Tests for django db application   "
                   "                                  <<<")
            print "^"*75            
            pass_to_django_manage([execname, 'test', 'db'])

    def complete_tests(self, subargs_idx, subargs):
        """
        I complete with subargs that were not used yet.
        """
        # I remove the one on which I am, so if I wrote all of it but
        # did not press space, it will get completed
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx+1:]
        # I create a list of the tests that are not already written on the 
        # command line
        remaining_tests = (
            set(self.allowed_test_folders) - set(other_subargs))

        return " ".join(sorted(remaining_tests))


    def get_querydict_from_keyvalue(self, key, separator_filter, value):
        from aiida.orm import (Node, Code, Data, Calculation,
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
        
        if item == 'i': # input
            keystring = "inputs"
            do_recursive = True
        elif item == 'o': # input
            keystring = "outputs"
            do_recursive = True
        elif item == 'p': # input
            keystring = "parents"
            do_recursive = True
        elif item == 'c': # input
            keystring = "children"
            do_recursive = True
        elif item == 'a': # input
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

        elif item == 'e': # input
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
            return ({key+sep_filter_string: value}, # all, including the dots
                    [key])

        if do_recursive:
            if sep:
                tempdict, templist = self.get_querydict_from_keyvalue(
                    subproperty, 
                    separator_filter,
                    value)
                # In this case the filter is added by the recursive function
                return ({"{}__{}".format(keystring, k): v 
                        for k,v in tempdict.iteritems()},
                        ["{}__{}".format(keystring, k) for k in templist] + 
                        ["{}__pk".format(keystring),
                         "{}__type".format(keystring),
                         "{}__label".format(keystring)],
                        )
            else:
                return ({keystring+sep_filter_string: value},
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
#        pieces = arg.split("=")
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
        load_django()
        from django.db.models import Q
        from aiida.djsite.db.models import DbNode
                
#        django_query = Q()
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
        
        print "*** DEBUG: QUERY ***" + "*"*52
        for (q,v), n in queries:
            print "* {}{}".format("[NEG]" if n else "", q)
        print "*" * 72
        
        for (query,values), negate in queries:
            
            all_values += list(values)
            if negate:
                if len(query) == 1:                
#                    django_query = django_query & ~Q(**query)
                    django_query = django_query.filter(~Q(**query))
                elif len(query) == 2:
                    
                    raise NotImplementedError("The current implementation does not work for negation of attributes. See comments in source code.")

                    ## NOT THE RIGHT WAY TO MANAGE NEGATIONS!! SEE AT THE
                    ## END OF THE FILE
                    temp = [(k, v) for k,v in query.iteritems()]
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

#In [11]: attr_res = DbAttribute.objects.filter(Q(key='cell.atoms'), ~Q(ival__gt=7))
#
#In [12]: dbres = DbNode.objects.filter(outputs__dbattributes__in=attr_res).distinct()
#
#In [13]: print dbres.query
#SELECT DISTINCT "db_dbnode"."id", "db_dbnode"."uuid", "db_dbnode"."type", "db_dbnode"."label", "db_dbnode"."description", "db_dbnode"."ctime", "db_dbnode"."mtime", "db_dbnode"."user_id", "db_dbnode"."dbcomputer_id", "db_dbnode"."nodeversion", "db_dbnode"."lastsyncedversion" FROM "db_dbnode" INNER JOIN "db_dblink" ON ("db_dbnode"."id" = "db_dblink"."input_id") INNER JOIN "db_dbnode" T3 ON ("db_dblink"."output_id" = T3."id") INNER JOIN "db_dbattribute" ON (T3."id" = "db_dbattribute"."dbnode_id") WHERE "db_dbattribute"."id" IN (SELECT U0."id" FROM "db_dbattribute" U0 WHERE (U0."key" = cell.atoms  AND NOT ((U0."ival" > 7  AND U0."ival" IS NOT NULL))))

## OR, if doing
#dbres = DbNode.objects.filter(dbattributes__in=attr_res).distinct()
#In [18]: print dbres.query
#SELECT DISTINCT "db_dbnode"."id", "db_dbnode"."uuid", "db_dbnode"."type", "db_dbnode"."label", "db_dbnode"."description", "db_dbnode"."ctime", "db_dbnode"."mtime", "db_dbnode"."user_id", "db_dbnode"."dbcomputer_id", "db_dbnode"."nodeversion", "db_dbnode"."lastsyncedversion" FROM "db_dbnode" INNER JOIN "db_dbattribute" ON ("db_dbnode"."id" = "db_dbattribute"."dbnode_id") WHERE "db_dbattribute"."id" IN (SELECT U0."id" FROM "db_dbattribute" U0 WHERE (U0."key" = cell.atoms  AND NOT ((U0."ival" > 7  AND U0."ival" IS NOT NULL))))

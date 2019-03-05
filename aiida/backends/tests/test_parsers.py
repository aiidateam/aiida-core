# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for specific subclasses of Data
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import io
import six
from six.moves import range

from aiida.backends.testbase import AiidaTestCase


### Here comparisons are defined #####################################
### Each comparison has to be a function with name
### _comparison_COMPARISONNAME
### and accepting three parameters:
### - testclass: the testing class, with the proper AssertXXX methods
### - the dbdata value, i.e. the value parsed by the test
### - comparisondata, the values specified by the user for comparison;
###   they typically contain a 'value', and possibly other keys for
###   more advanced keys
def _comparison_AlmostEqual(testclass, dbdata, comparisondata):
    """
    Compare two numbers (or a list of numbers) to check that
    they are all almost equal (within a default precision of 7 digits)
    """
    value = comparisondata['value']
    if isinstance(dbdata, (list, tuple)) and isinstance(value, (list, tuple)):
        testclass.assertEqual(len(dbdata), len(value))
        for i in range(len(dbdata)):
            testclass.assertAlmostEqual(dbdata[i], value[i])
    else:
        testclass.assertAlmostEqual(dbdata, value)


def _comparison_Equal(testclass, dbdata, comparisondata):
    """
    Compare two objects to see if they are equal
    """
    testclass.assertEqual(dbdata, comparisondata['value'])


def _comparison_LengthEqual(testclass, dbdata, comparisondata):
    """
    Check if the length of the object is equal to the value specified
    """
    testclass.assertEqual(len(dbdata), comparisondata['value'])


### End of comparison definition #####################################


def output_test(pk, testname, skip_uuids_from_inputs=[]):
    """
    This is the function that should be used to create a new test from an
    existing calculation.

    It is possible to simplify the file removing unwanted nodes.

    :param pk: PK of Calculation, used for test
    :param testname: the name of this test, used to create a new folder.
        The folder name will be of the form test_PLUGIN_TESTNAME,
        with PLUGIN substituted by the plugin name, with dots replaced by
        underscores. Testname can contain only digits, letters and underscores.
    :param skip_uuids_from_inputs: a list of UUIDs of input nodes to be
        skipped
    """
    import os
    from aiida.common import json

    from aiida.common.folders import Folder
    from aiida.orm import CalcJobNode
    from aiida.orm.utils import load_node
    from aiida.orm.importexport import export_tree
    
    c = load_node(pk, sub_classes=(CalcJobNode,))
    outfolder = "test_{}_{}".format(
        c.get_option('parser_name').replace('.', '_'),
        testname)

    if not is_valid_folder_name(outfolder):
        raise ValueError("The testname is invalid; it can contain only letters, digits or underscores")

    if os.path.exists(outfolder):
        raise ValueError("Out folder '{}' already exists".format(outfolder))

    inputs = []
    for entry in c.get_incoming().all():
        if entry.node.uuid not in skip_uuids_from_inputs:
            inputs.append(entry.node.dbmodel)

    folder = Folder(outfolder)
    to_export = [c.dbnode] + inputs
    try:
        to_export.append(c.outputs.retrieved.dbnode)
    except AttributeError:
        raise ValueError("No output retrieved node; without it, we cannot test the parser!")
    export_tree(to_export, folder=folder, also_parents=False, also_calc_outputs=False)

    # Create an empty checks file
    with io.open(os.path.join(outfolder, '_aiida_checks.json'), 'wb') as fhandle:
        json.dump({}, fhandle)

    for path, dirlist, filelist in os.walk(outfolder):
        if len(dirlist) == 0 and len(filelist) == 0:
            with io.open("{}/.gitignore".format(path), 'w', encoding='utf8') as fhandle:
                fhandle.write(u"# This is a placeholder file, used to make git store an empty folder")
                fhandle.flush()


def is_valid_folder_name(name):
    """
    Return True if the string (that will be the folder name of each subtest)
    is a valid name for a test function: it should start with ``test_``, and
    contain only letters, digits or underscores.
    """
    import string

    if not name.startswith('test_'):
        return False

    # Remove valid characters, see if anything remains, allow only ASCII strings here
    bad_characters = name.translate(None, string.ascii_letters + string.digits + '_')
    if bad_characters:
        return False

    return True


class _TestParserMeta(type):
    """
    Some python black magic to dynamically create tests
    """

    def __new__(cls, name, bases, attrs):
        import os

        newcls = type.__new__(cls, name, bases, attrs)

        file_folder = os.path.split(__file__)[0]
        parser_test_folder = os.path.join(file_folder, 'parser_tests')
        if os.path.isdir(parser_test_folder):
            for f in os.listdir(parser_test_folder):
                absf = os.path.abspath(os.path.join(parser_test_folder, f))
                if is_valid_folder_name(f) and os.path.isdir(absf):
                    function_name = f
                    setattr(newcls, function_name, newcls.return_base_test(absf))

        return newcls


@six.add_metaclass(_TestParserMeta)
class TestParsers(AiidaTestCase):
    """
    This class dynamically finds all tests in a given subfolder, and loads
    them as different tests.
    """
    # To have both the "default" error message from assertXXX, and the
    # msg specified by us
    longMessage = True

    def read_test(self, outfolder):
        import os
        import importlib
        from aiida.common import json

        from aiida.orm import CalcJobNode
        from aiida.orm.utils import load_node
        from aiida.orm.importexport import import_data

        imported = import_data(outfolder, ignore_unknown_nodes=True, silent=True)

        calc = None
        for _, pk in imported['aiida.backends.djsite.db.models.DbNode']['new']:
            c = load_node(pk)
            if issubclass(c.__class__, CalcJobNode):
                calc = c
                break

        retrieved = calc.outputs.retrieved

        try:
            with io.open(os.path.join(outfolder, '_aiida_checks.json', encoding='utf8')) as fhandle:
                tests = json.load(f)
        except IOError:
            raise ValueError("This test does not provide a check file!")
        except ValueError:
            raise ValueError("This test does provide a check file, but it cannot be JSON-decoded!")

        mod_path = 'aiida.backends.tests.parser_tests.{}'.format(os.path.split(outfolder)[1])

        skip_test = False
        try:
            m = importlib.import_module(mod_path)
            skip_test = m.skip_condition()
        except Exception:
            pass

        if skip_test:
            raise SkipTestException

        return calc, {'retrieved': retrieved}, tests

    @classmethod
    def return_base_test(cls, folder):
        from inspect import isfunction

        def base_test(self):
            try:
                calc, retrieved_nodes, tests = self.read_test(folder)
            except SkipTestException:
                return None
            Parser = calc.get_parser_class()
            if Parser is None:
                raise NotImplementedError
            else:
                parser = Parser(calc)
                successful, new_nodes_tuple = parser.parse_with_retrieved(retrieved_nodes)
                self.assertTrue(successful, msg="The parser did not succeed")
                parsed_output_nodes = dict(new_nodes_tuple)

                # All main keys: name of nodes that should be present
                for test_node_name in tests:
                    try:
                        test_node = parsed_output_nodes[test_node_name]
                    except KeyError:
                        raise AssertionError("Output node '{}' expected but not found".format(test_node_name))

                    # Each subkey: attribute to check
                    # attr_test is the name of the attribute
                    for attr_test in tests[test_node_name]:
                        try:
                            dbdata = test_node.get_attribute(attr_test)
                        except AttributeError:
                            raise AssertionError("Attribute '{}' not found in "
                                                 "parsed node '{}'".format(attr_test, test_node_name))
                        # Test data from the JSON
                        attr_test_listtests = tests[test_node_name][attr_test]
                        for test_number, attr_test_data in enumerate(attr_test_listtests, start=1):
                            try:
                                comparison = attr_test_data.pop('comparison')
                            except KeyError as exc:
                                raise ValueError("Missing '{}' in the '{}' field "
                                                 "in '{}' in "
                                                 "the test file".format(exc.args[0], attr_test, test_node_name))

                            try:
                                comparison_test = globals()["_comparison_{}".format(comparison)]
                            except KeyError:
                                raise ValueError("Unsupported '{}' comparison in "
                                                 "the '{}' field in '{}' in "
                                                 "the test file".format(comparison, attr_test, test_node_name))

                            if not isfunction(comparison_test):
                                raise TypeError("Internal error: the variable _comparison_{} is not a "
                                                "function!".format(comparison))

                            try:
                                comparison_test(testclass=self, dbdata=dbdata, comparisondata=attr_test_data)
                            except Exception as e:
                                # Probably, a 'better' way should be found to do this!
                                if e.args:
                                    e.args = tuple([
                                        "Failed test #{} for {}->{}: {}".format(test_number, test_node_name, attr_test,
                                                                                e.args[0])
                                    ] + list(e.args[1:]))
                                raise e

        return base_test


class SkipTestException(Exception):
    pass

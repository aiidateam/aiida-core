# -*- coding: utf-8 -*-
"""
Tests for specific subclasses of Data
"""
from django.utils import unittest

from aiida.orm import Node
from aiida.common.exceptions import ModificationNotAllowed, UniquenessError
from aiida.djsite.db.testbase import AiidaTestCase

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Andrius Merkys"


def output_test(pk, outfolder, skip_uuids_from_inputs=[]):
    """
    This is the function that should be used to create a new test from an
    existing calculation.
    
    It is possible to simplify the file removing unwanted nodes. 
    
    :param pk: PK of Calculation, used for test
    :param outfolder: folder to place the test files
    :param skip_uuids_from_inputs: a list of UUIDs of input nodes to be
        skipped

    .. todo:: create a test case to test the generation of GIT placeholders
        for empty folders (.gitignore with comments)
    """
    from aiida.orm import JobCalculation
    from aiida.common.folders import Folder
    from aiida.cmdline.commands.exportfile import export_tree
    import os
    import json

    if os.path.exists(outfolder):
        raise ValueError("Out folder '{}' already exists".format(outfolder))

    c = JobCalculation.get_subclass_from_pk(pk)
    inputs = []
    for node in c.get_inputs():
        if node.uuid not in skip_uuids_from_inputs:
            inputs.append(node.dbnode)

    folder = Folder(outfolder)
    export_tree([c.dbnode] + inputs, folder=folder, also_parents=False)

    # Create an empty checks file
    with open(os.path.join(outfolder, '_aiida_checks.json'), 'w') as f:
        json.dump({}, f)

    for path, dirlist, filelist in os.walk(outfolder):
        if len(dirlist) == 0 and len(filelist) == 0:
            with open("{}/.gitignore".format(path), 'w') as f:
                f.write("# This is a placeholder file, used to make git "
                        "store an empty folder")
                f.flush()


def read_test(outfolder):
    """
    Read a test folder created by output_test.

    .. note:: This method should only be called in the testing
        environment, because it's importing data in the current
        database.
    """
    import os
    import json

    from aiida.orm import JobCalculation,load_node
    from aiida.common.exceptions import NotExistent
    from aiida.cmdline.commands.importfile import import_file

    imported = import_file(outfolder,format='tree',
                           ignore_unknown_nodes=True,silent=True)

    calc = None
    for _,pk in imported['aiida.djsite.db.models.DbNode']['new']:
        c = load_node(pk)
        if issubclass(c.__class__,JobCalculation):
            calc = c
            break

    retrieved = calc.out.retrieved

    try:
        with open(os.path.join(outfolder, '_aiida_checks.json')) as f:
            tests = json.load(f)
    except IOError:
        raise ValueError("This test does not provide a check file!")
    except ValueError:
        raise ValueError("This test does provide a check file, but it cannot "
                         "be JSON-decoded!")
    
    return calc, {'retrieved': retrieved}, tests


def is_valid_folder_name(name):
    """
    Return True if the string (that will be the folder name of each subtest)
    is a valid name for a test function: it should start with test_, and
    contain only letters, digits or underscores.
    """
    import string

    if not name.startswith('test_'):
        return False

    # Remove valid characters, see if anything remains
    bad_characters = name.translate(None, string.letters + string.digits + '_')
    if bad_characters:
        return False

    return True


class TestParsers(AiidaTestCase):
    """
    This class dynamically finds all tests in a given subfolder, and loads
    them as different tests.
    """
    # To have both the "default" error message from assertXXX, and the 
    # msg specified by us
    longMessage = True

    @classmethod
    def return_base_test(cls, folder):

        def base_test(self):
            calc, retrieved_nodes, tests = read_test(folder)
            Parser = calc.get_parserclass()
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
                        raise AssertionError("Output node '{}' expected but "
                                             "not found".format(test_node_name))

                    # Each subkey: attribute to check
                    # attr_test is the name of the attribute
                    for attr_test in tests[test_node_name]:
                        try:
                            dbdata = test_node.get_attr(attr_test)
                        except AttributeError:
                            raise AssertionError("Attribute '{}' not found in "
                                                 "parsed node '{}'".format(attr_test,
                                                                           test_node_name))
                        # Test data from the JSON
                        attr_test_data = tests[test_node_name][attr_test]
                        try:
                            comparison = attr_test_data['comparison']
                            value = attr_test_data['value']
                        except TypeError:
                            raise ValueError("Malformed '{}' field in '{}' in "
                                             "the test file".format(attr_test, test_node_name))
                        except KeyError as e:
                            raise ValueError("Missing '{}' in the '{}' field "
                                             "in '{}' in "
                                             "the test file".format(e.message,
                                                                    attr_test, test_node_name))
                        if comparison == "AlmostEqual":
                            if isinstance(dbdata, list) and isinstance(value, list):
                                self.assertEqual(len(dbdata), len(value),
                                                 msg="Failed test for {}->{}".format(
                                                     test_node_name, attr_test))
                                for i in range(0, len(dbdata)):
                                    self.assertAlmostEqual(dbdata[i], value[i],
                                                           msg="Failed test for {}->{}".format(
                                                               test_node_name, attr_test))
                            else:
                                self.assertAlmostEqual(dbdata, value,
                                                       msg="Failed test for {}->{}".format(
                                                           test_node_name, attr_test))
                        elif comparison == "Equal":
                            self.assertEqual(dbdata, value,
                                             msg="Failed test for {}->{}".format(
                                                 test_node_name, attr_test))
                        else:
                            raise ValueError("Unsupported'{}' comparison in "
                                             "the '{}' field in '{}' in "
                                             "the test file".format(comparison,
                                                                    attr_test, test_node_name))

        return base_test

    class __metaclass__(type):
        """
        Some python black magic to dynamically create tests
        """

        def __new__(cls, name, bases, attrs):
            import os

            newcls = type.__new__(cls, name, bases, attrs)

            file_folder = os.path.split(__file__)[0]
            parser_test_folder = os.path.join(file_folder, 'parser_tests')
            for f in os.listdir(parser_test_folder):
                absf = os.path.abspath(os.path.join(parser_test_folder, f))
                if is_valid_folder_name(f) and os.path.isdir(absf):
                    function_name = f
                    setattr(newcls, function_name,
                            newcls.return_base_test(absf))

            return newcls

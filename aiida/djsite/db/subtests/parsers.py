# -*- coding: utf-8 -*-
"""
Tests for specific subclasses of Data
"""
from django.utils import unittest

from aiida.orm import Node
from aiida.common.exceptions import ModificationNotAllowed, UniquenessError
from aiida.djsite.db.testbase import AiidaTestCase
        
__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.3.0"

def pre_encoder(data):
    """
    Pre_encode data to make it possible to store in a JSON and easy
    to parse back.
    Only differences between standard JSON is that any string is prepended
    by "S", and datetimes are converted to strings starting with "D", so 
    that when decoding and finding a string, one can understand if it is a 
    date or a string by reading the first character.
    """
    import datetime

    if isinstance(data, (list, tuple)):
        return [pre_encoder(_) for _ in data]
    elif isinstance(data, dict):
        return {k: pre_encoder(v) for k, v in data.iteritems()}
    elif isinstance(data, str):
        return "S{}".format(data)
    elif isinstance(data, unicode):
        return u"S{}".format(data)
    elif isinstance(data, datetime.datetime):
        return data.strftime('D%Y-%m-%dT%H:%M:%S.%f%z')
    else:
        return data

def post_decoder(data):
    """
    Reverts the encoding done by the pre_encoder
    """
    if isinstance(data, (list, tuple)):
        return [post_decoder(_) for _ in data]
    elif isinstance(data, dict):
        return {k: post_decoder(v) for k, v in data.iteritems()}
    elif isinstance(data, basestring):
        if data.startswith("S"):
            # Starting with S: it is an encoded string
            return data[1:]
        elif data.startswith("D"):
            # It is a date
            
            # OLD implementation: it also includes the check of the timezone
            # but requires a new dependency of AiiDA on dateutil: 
            # that would need to be added in the requirements.txt
            #import dateutil.parser
            #return dateutil.parser.parse(data[1:])
            
            # New one lacks time zone, but it should be enough for the test
            import time
            return time.strptime(data[1:],"%Y-%m-%dT%H:%M:%S.%f+0000")
        else:
            # Strange encoding char, error!
            raise ValueError("Unknown encode character! ({})".format(data[:1]))
    else:
        return data

def serialize_dict(dictionary, f):
    """
    Serialize a dictionary. Converts to JSON, passing first through the
    pre_encoder
    """
    import json
    return json.dump(pre_encoder(dictionary), f, indent=2)

def deserialize_dict(f):
    """
    Desrialize a dictionary. Reads a JSON, and passes it through the
    post_decoder before returning.
    """
    import json
    return post_decoder(json.load(f))

def serialize_node(node, destfolder):
    """
    Serialize a node in a given folder.
    """
    import os, shutil
    from django.db import models

    if os.path.exists(destfolder):
        raise ValueError("Destination folder '{}' "
            "already exists.".format(destfolder))

    try:
        os.makedirs(destfolder)
    except OSError:
        pass # Directory already exists (should actually check for errno=17)

    shutil.copytree(node.folder.abspath, os.path.join(destfolder, 'data'))
    
    attributes = dict(node.iterattrs())
    with open(os.path.join(destfolder,'_aiida_attributes.aiidajson'), 'w') as f:
        serialize_dict(attributes,f)
        
    nodedata = {f.name: getattr(node.dbnode, f.name)
                for f in node.dbnode._meta.fields
                if not isinstance(getattr(node.dbnode, f.name), models.Model)
                and f.name != 'id'}
    with open(os.path.join(destfolder,'_aiida_nodedata.aiidajson'), 'w') as f:
        serialize_dict(nodedata,f)

def deserialize_node(folder):
    """
    Deserialize a single node, from its folder.
    """
    import os, shutil
    from aiida.orm.node import from_type_to_pluginclassname
    from aiida.common.pluginloader import load_plugin
    from aiida.common.exceptions import DbContentError, MissingPluginError

    with open(os.path.join(folder,'_aiida_attributes.aiidajson')) as f:
        attributes = deserialize_dict(f)

    with open(os.path.join(folder,'_aiida_nodedata.aiidajson')) as f:
        nodedata = deserialize_dict(f)

    try:
        pluginclassname = from_type_to_pluginclassname(nodedata['type'])
    except DbContentError:
        raise DbContentError("The type name of imported node is "
                             "not valid: '{}'".format(nodedata['type']))

    try:
        PluginClass = load_plugin(Node, 'aiida.orm', pluginclassname)
    except MissingPluginError:
        raise DbContentError("Unable to find plugin for type '{}' (uuid={}), "
                             "will use base Node class".format(
                            nodedata['type'], nodedata['uuid']))
        PluginClass = Node
        
    n = PluginClass()

    for k, v in nodedata.iteritems():
        if k != 'type':
            setattr(n._dbnode, k, v)
        
    for k, v in attributes.iteritems():
        n._set_attr(k, v)
                
    # Fully replace the directory
    shutil.rmtree(n.folder.abspath)
    src = os.path.abspath(os.path.join(folder, 'data'))
    shutil.copytree(src, n.folder.abspath)

    return n

def output_test(pk, outfolder):
    """
    This is the function that should be used to create a new test from an
    existing calculation.
    
    It is possible to simplify the file removing unwanted nodes. 
    
    .. todo:: manage empty folders, that are not saved by GIT!
       A temporary solution to find them and add a placeholder file::
   
        find . -type d -empty -print0 | xargs -0 -n1 -IXXX touch XXX/.placeholder

    One has then to create a suitable test file.
    """
    from aiida.orm import JobCalculation
    import os
    import json
    if os.path.exists(outfolder):
        raise ValueError("Out folder '{}' already exists".format(outfolder))

    c = JobCalculation.get_subclass_from_pk(pk)
    inputs = c.get_inputs_dict()
    serialize_node(c, destfolder=os.path.join(outfolder,c.uuid))
    
    for n in inputs.itervalues():
        serialize_node(n, destfolder=os.path.join(outfolder,n.uuid))
    
    linkname = c._get_linkname_retrieved()
    # Should instead get all retrieved nodes, see the calcinfo!
    retrieved = c.get_outputs_dict()[linkname]
    serialize_node(retrieved, destfolder=os.path.join(outfolder,retrieved.uuid))

    links = {'calc': c.uuid,
         'inputs': {k: v.uuid for k, v in inputs.iteritems()},
         'retrieved': {'uuid': retrieved.uuid, 'linkname': linkname}}

    with open(os.path.join(outfolder,'_aiida_linkdata.json'), 'w') as f:
        json.dump(links,f,indent=2)

    # Create an empty checks file
    with open(os.path.join(outfolder,'_aiida_checks.json'), 'w') as f:
        json.dump({},f)

    import sys
    print >> sys.stderr, "WARNING! Empty folders are not stored by GIT!! This needs to be fixed."
        
def read_test(outfolder):
    """
    Read a test folder created by output_test
    """
    import os
    import json
    
    with open(os.path.join(outfolder,'_aiida_linkdata.json')) as f:
        linkdata = json.load(f)

    calc = deserialize_node(os.path.join(outfolder,linkdata['calc']))
    inputs = {}
    for k, v in linkdata['inputs'].iteritems():
        inputs[k] = deserialize_node(os.path.join(outfolder, v))
    retrieved = deserialize_node(os.path.join(outfolder,
        linkdata['retrieved']['uuid']))

    retrieved._add_link_from(calc, label=linkdata['retrieved']['linkname'])
    for inputname, inputnode in inputs.iteritems():
        calc._add_link_from(inputnode, label=inputname)
    
    try:
        with open(os.path.join(outfolder,'_aiida_checks.json')) as f:
            tests = json.load(f)
    except IOError:
        raise ValueError("This test does not provide a check file!")
    except ValueError:
        raise ValueError("This test does provide a check file, but it cannot "
                         "be JSON-decoded!")
    
    return calc, {linkdata['retrieved']['linkname']: retrieved}, tests

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
                            self.assertAlmostEqual(dbdata,value,
                                msg="Failed test for {}->{}".format(
                                    test_node_name, attr_test))
                        elif comparison == "Equal":
                            self.assertEqual(dbdata,value,
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
        
        

# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import os
import subprocess as sp
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.cmdline.commands.cmd_node import node_delete, node_label, node_description, show, tree, repo_ls, repo_cat

class TestVerdiNode(AiidaTestCase):

    node_labels = ('in1', 'in2', 'wf', 'slave1', 'slave2', 'outp1', 'outp2', 'outp3', 'outp4')

    def setUp(self):
        """Sets up a few nodes to play around with."""
        from aiida.orm import Node

        nodes = { key : Node().store() for key in self.node_labels }

        nodes['wf'].add_link_from(nodes['in1'], link_type=LinkType.INPUT)
        nodes['slave1'].add_link_from(nodes['in1'], link_type=LinkType.INPUT)
        nodes['slave1'].add_link_from(nodes['in2'], link_type=LinkType.INPUT)
        nodes['slave2'].add_link_from(nodes['in2'], link_type=LinkType.INPUT)
        nodes['slave1'].add_link_from(nodes['wf'], link_type=LinkType.CALL)
        nodes['slave2'].add_link_from(nodes['wf'], link_type=LinkType.CALL)
        nodes['outp1'].add_link_from(nodes['slave1'], link_type=LinkType.CREATE)
        nodes['outp2'].add_link_from(nodes['slave2'], link_type=LinkType.CREATE)
        nodes['outp2'].add_link_from(nodes['wf'], link_type=LinkType.RETURN)
        nodes['outp3'].add_link_from(nodes['wf'], link_type=LinkType.CREATE)
        nodes['outp4'].add_link_from(nodes['wf'], link_type=LinkType.RETURN)
        self.nodes = nodes

        self.runner = CliRunner()

    def test_node_delete(self):
        """Test it deletes nodes down the provenance.
        
        See also backends/tests/nodes.py."""
        nodes = self.nodes
        options = [str(nodes['in1'].pk), '-v']
        user_input = '\n'.join(['Y'])
        result = self.runner.invoke(node_delete, options, input=user_input)
        self.assertIsNone(result.exception)

        for label in ['in1', 'wf', 'slave1', 'outp1', 'outp3']:
            node = nodes[label]
            self.assertTrue(str(node.uuid) in result.output, "Node {} should be deleted".format(label))

    def test_node_delete_non_interactive(self):
        """Test it deletes nodes down the provenance.
        
        See also backends/tests/nodes.py."""
        nodes = self.nodes
        options = [str(nodes['in1'].pk), '-v', '--non-interactive']
        result = self.runner.invoke(node_delete, options)
        self.assertIsNone(result.exception)

    def test_node_show(self):
        nodes = self.nodes
        options = [str(nodes['in1'].pk), '--print-groups']
        result = self.runner.invoke(show, options)
        self.assertIsNone(result.exception)

        self.assertTrue(str(nodes['in1'].uuid) in result.output)

    def test_node_tree(self):
        nodes = self.nodes
        options = [str(nodes['in1'].pk), '-d', 3]
        result = self.runner.invoke(tree, options)
        self.assertIsNone(result.exception)

        self.assertTrue(str(nodes['in1'].uuid) in result.output)
        self.assertTrue(str(nodes['outp3'].pk) in result.output)
        self.assertTrue(str(nodes['in2'].uuid) not in result.output)

    def test_node_label(self):
        node = self.nodes['in1']
        label = u"my label"
        node.label = label
        node.store()
        
        # read existing label
        options = [str(node.pk), '--raw']
        result = self.runner.invoke(node_label, options)
        self.assertIsNone(result.exception)
        self.assertEquals(result.output, label+'\n')

        # set new label
        new_label = "my new label"
        options = [str(node.pk), '--label', new_label, '--force']
        result = self.runner.invoke(node_label, options)
        self.assertIsNone(result.exception)

        from aiida.orm import load_node
        updated_node = load_node(node.pk)
        self.assertEquals(updated_node.label, new_label)

    def test_node_description(self):
        node = self.nodes['in1']
        description = u"my desc\nover two lines"
        node.description = description
        node.store()
        
        options = [str(node.pk), '--raw']
        result = self.runner.invoke(node_description, options)
        self.assertIsNone(result.exception)
        self.assertEquals(result.output, description+'\n')


class TestVerdiNodeRepo(AiidaTestCase):

    def setUp(self):
        """Sets up a few nodes to play around with."""
        from aiida.orm.data.singlefile import SinglefileData
        import tempfile

        file_content = '''file-with-contents'''

        with tempfile.NamedTemporaryFile(mode='w+') as f:
            f.write(file_content)
            f.flush()
            node = SinglefileData(file=f.name)
            node.store()

        self.node = node
        self.file_content = file_content

        self.runner = CliRunner()

    def test_node_repo_ls(self):
        options = [str(self.node.pk)]
        result = self.runner.invoke(repo_ls, options)
        self.assertIsNone(result.exception)

        options = [str(self.node.pk), 'non-existent-path']
        result = self.runner.invoke(repo_ls, options)
        self.assertIsNotNone(result.exception)

    def test_node_repo_cat(self):
        options = [str(self.node.pk), "path/" + self.node.filename]
        result = self.runner.invoke(repo_cat, options)
        self.assertIsNone(result.exception)
        self.assertEquals(self.file_content, result.output)

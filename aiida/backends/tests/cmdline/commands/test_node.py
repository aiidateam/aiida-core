import os
import subprocess as sp
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.cmdline.commands.node import node_delete

class TestVerdiNode(AiidaTestCase):

    node_labels = ('in1', 'in2', 'wf', 'slave1', 'slave2', 'outp1', 'outp2', 'outp3', 'outp4')

    @classmethod
    def setUpClass(cls):
        super(TestVerdiNode, cls).setUpClass()
        from aiida.orm import Computer
        new_comp = Computer(name='comp',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='direct',
                                workdir='/tmp/aiida')
        new_comp.store()



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
        
        See alo backends/tests/nodes.py."""
        nodes = self.nodes
        options = [str(nodes['in1'].pk), '-v']
        user_input = '\n'.join(['Y'])
        result = self.runner.invoke(node_delete, options, input=user_input)
        self.assertIsNone(result.exception)

        for label in ['in1', 'wf', 'slave1', 'outp1', 'outp3']:
            node = nodes[label]
            self.assertTrue(str(node.uuid) in result.output, "Node {} should be deleted".format(label))


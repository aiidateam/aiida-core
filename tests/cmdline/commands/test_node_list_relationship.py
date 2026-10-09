###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the relationship filters in `verdi node list`."""
import pytest
from aiida import orm
from aiida.common.links import LinkType
from aiida.cmdline.commands import cmd_node

@pytest.fixture
def provenance_graph(aiida_profile_clean, aiida_localhost):
    """Create a simple provenance graph for testing.
    
    A (Data) --[input]--> B (CalcJob) --[create]--> C (Data)
    """
    node_a = orm.Data().store()
    node_a.label = 'node_a'
    node_a.store()
    
    node_b = orm.CalcJobNode(computer=aiida_localhost)
    node_b.label = 'node_b'
    node_b.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    node_b.base.links.add_incoming(node_a, link_type=LinkType.INPUT_CALC, link_label='link_ab')
    node_b.store()
    
    node_c = orm.Data()
    node_c.label = 'node_c'
    node_c.base.links.add_incoming(node_b, link_type=LinkType.CREATE, link_label='link_bc')
    node_c.store()
    
    return node_a, node_b, node_c

def test_node_list_ancestor(run_cli_command, provenance_graph):
    """Test the `--ancestor` filter."""
    node_a, node_b, node_c = provenance_graph
    
    # List nodes that have node_a as an ancestor. Should be node_b and node_c.
    options = ['--ancestor', str(node_a.pk), '--project', 'label', '--raw']
    result = run_cli_command(cmd_node.node_list, options)
    
    labels = result.output.strip().split('\n')
    assert 'node_b' in labels
    assert 'node_c' in labels
    assert 'node_a' not in labels

def test_node_list_descendant(run_cli_command, provenance_graph):
    """Test the `--descendant` filter."""
    node_a, node_b, node_c = provenance_graph
    
    # List nodes that have node_c as a descendant. Should be node_a and node_b.
    options = ['--descendant', str(node_c.pk), '--project', 'label', '--raw']
    result = run_cli_command(cmd_node.node_list, options)
    
    labels = result.output.strip().split('\n')
    assert 'node_a' in labels
    assert 'node_b' in labels
    assert 'node_c' not in labels

def test_node_list_both_filters(run_cli_command, provenance_graph):
    """Test both `--ancestor` and `--descendant` filters combined."""
    node_a, node_b, node_c = provenance_graph
    
    # List nodes that have node_a as ancestor AND node_c as descendant. Should be node_b.
    options = ['--ancestor', str(node_a.pk), '--descendant', str(node_c.pk), '--project', 'label', '--raw']
    result = run_cli_command(cmd_node.node_list, options)
    
    labels = result.output.strip().split('\n')
    assert labels == ['node_b']

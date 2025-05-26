###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the dumping of profile data to disk."""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import pytest

from aiida import load_profile, orm
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.dumping.config import DumpConfig, DumpMode

from .utils import compare_tree

# TODO: Also verify the log updates
# TODO: Verify Computer/code selection

# NOTE: There exists `create_file_hierarchy` and `serialize_file_hierarchy` fixtures

logger = AIIDA_LOGGER.getChild('tools.dumping.tests')

profile_dump_label = 'profile-dump'
add_group_label = 'add-group'
multiply_add_group_label = 'multiply-add-group'
sub_calc_group_label = 'sub-calc-group'

# --- Content Definitions for Dumped Nodes ---

_ADD_CALC_INPUT_CONTENT = [
    '_aiidasubmit.sh',
    'aiida.in',
    {'.aiida': ['calcinfo.json', 'job_tmpl.json']},
]

_ADD_CALC_OUTPUT_CONTENT = [
    '_scheduler-stderr.txt',
    '_scheduler-stdout.txt',
    'aiida.out',
]

# Content for a simple calculation node like ArithmeticAddCalculation
_ADD_CALC_NODE_CONTENT = [
    '.aiida_dump_safeguard',
    'aiida_node_metadata.yaml',
    {'inputs': _ADD_CALC_INPUT_CONTENT},
    {'outputs': _ADD_CALC_OUTPUT_CONTENT},
]

# Content for a simple function node like 'multiply'
_MULTIPLY_FUNC_NODE_CONTENT = [
    'aiida_node_metadata.yaml',
    '.aiida_dump_safeguard',
    {'inputs': ['source_file']},  # Assuming multiply function only has this repo file
]

# --- Content Definitions for IO Calc Nodes ---
_IO_CALC_INPUT_REPO_CONTENT = ['file.txt']
_IO_CALC_INPUT_NODE_CONTENT = [
    {'arraydata': ['default.npy']},
    {'folderdata': [{'relative_path': ['file.txt']}]},  # Represents FolderData repository
    {'singlefile': ['file.txt']},
]
_IO_CALC_OUTPUT_NODE_CONTENT = [
    {'folderdata': [{'relative_path': ['file.txt']}]},
    {'singlefile': ['file.txt']},
]

# Content list for a standard nested dump of the IO Calc
_IO_CALC_NODE_CONTENT_NESTED = [
    '.aiida_dump_safeguard',
    'aiida_node_metadata.yaml',
    {'inputs': _IO_CALC_INPUT_REPO_CONTENT},
    {'node_inputs': _IO_CALC_INPUT_NODE_CONTENT},
    {'node_outputs': _IO_CALC_OUTPUT_NODE_CONTENT},
]

_IO_CALC_NODE_CONTENT_NESTED_NO_OUTPUTS = [
    '.aiida_dump_safeguard',
    'aiida_node_metadata.yaml',
    {'inputs': _IO_CALC_INPUT_REPO_CONTENT},
    {'node_inputs': _IO_CALC_INPUT_NODE_CONTENT},
    # No 'node_outputs' key here
]

_IO_CALC_NODE_CONTENT_FLAT = [
    'README.md',
    'aiida_dump_log.json',
    '.aiida_dump_safeguard',
    'aiida_node_metadata.yaml',
    'file.txt',
    'default.npy',
]


# --- Dynamic Node Tree Generation Helpers ---
def get_expected_io_calc_tree(pk: int, process_label: str = 'CalculationNodeWithIO') -> Dict[str, List[Any]]:
    """Generates the expected nested dump tree dict for the IO CalculationNode."""
    node_dir_name = f'{process_label}-{pk}'
    return {node_dir_name: _IO_CALC_NODE_CONTENT_NESTED}


def get_expected_io_calc_tree_flat(pk: int, process_label: str = 'CalculationNodeWithIO') -> Dict[str, List[Any]]:
    """Generates the expected flat dump tree dict for the IO CalculationNode."""
    node_dir_name = f'{process_label}-{pk}'
    return {node_dir_name: _IO_CALC_NODE_CONTENT_FLAT}


def get_expected_add_calc_tree(pk: int) -> Dict[str, List[Any]]:
    """Generates the expected dump tree dict for an ArithmeticAddCalculation."""
    node_dir_name = f'ArithmeticAddCalculation-{pk}'
    return {node_dir_name: _ADD_CALC_NODE_CONTENT}


def get_expected_multiply_func_tree(pk: int) -> Dict[str, List[Any]]:
    """Generates the expected dump tree dict for a 'multiply' function node."""
    node_dir_name = f'multiply-{pk}'  # Assuming 'multiply' is the consistent label part
    return {node_dir_name: _MULTIPLY_FUNC_NODE_CONTENT}


def get_expected_multiply_add_wc_tree(wc_pk: int, child_pks: Tuple[int, int]) -> Dict[str, List[Any]]:
    """Generates the expected dump tree dict for a MultiplyAddWorkChain."""
    wc_process_label = 'MultiplyAddWorkChain'
    node_dir_name = f'{wc_process_label}-{wc_pk}'
    multiply_pk, add_pk = child_pks

    # Get the tree structures for children using their helpers
    multiply_child_tree = get_expected_multiply_func_tree(multiply_pk)
    add_child_tree = get_expected_add_calc_tree(add_pk)

    # Extract keys to use in parent structure (assumes '01-' and '02-' prefixes)
    multiply_dir_key = next(iter(multiply_child_tree.keys()))
    add_dir_key = next(iter(add_child_tree.keys()))

    return {
        node_dir_name: [
            '.aiida_dump_safeguard',
            'aiida_node_metadata.yaml',
            {f'01-{multiply_dir_key}': multiply_child_tree[multiply_dir_key]},
            {f'02-{add_dir_key}': add_child_tree[add_dir_key]},
        ]
    }


# --- Helper for the WorkChain with IO children ---
def get_expected_io_wc_tree(
    wc_pk: int,
    child_pks: Tuple[int, int],  # Expecting PKs of the two IO Calcs
    wc_process_label: str = 'WorkChainNodeWithIO',  # Assumed label for the test WC
    child_process_label: str = 'CalculationNodeWithIO',  # Assumed label for the IO calcs
) -> Dict[str, List[Any]]:
    """
    Generates the expected dump tree for the test WorkChain with IO children.
    Assumes two children called in sequence.
    """
    wc_node_dir_name = f'{wc_process_label}-{wc_pk}'

    # Get the tree structures for the children using their specific helper
    # Note: We use the *content* list (_IO_CALC_NODE_CONTENT_NESTED) directly
    #       to avoid creating intermediate single-node dicts here.
    child1_dir_name = f'{child_process_label}-{child_pks[0]}'
    child2_dir_name = f'{child_process_label}-{child_pks[1]}'

    wc_content = [
        '.aiida_dump_safeguard',
        'aiida_node_metadata.yaml',
        # Nest child 1 (assuming 01- prefix)
        {
            f'01-{child1_dir_name}': _IO_CALC_NODE_CONTENT_NESTED  # Use the predefined content list
        },
        # Nest child 2 (assuming 02- prefix)
        {
            f'02-{child2_dir_name}': _IO_CALC_NODE_CONTENT_NESTED  # Use the predefined content list
        },
    ]

    return {wc_node_dir_name: wc_content}


# --- Helper for the specific nested WorkChain with IO children ---
def get_expected_nested_io_wc_tree(
    wc_pk: int,
    wc_sub_pk: int,
    child_calc_pks: Tuple[int, int],  # Expecting PKs of the two IO Calcs called by sub-WC
    wc_process_label: str = 'WorkflowNode',  # Default from fixture
    # Labels below are NOT used for nested directory names, only PKs are.
    wc_sub_process_label: str = 'WorkflowNode',  # Default from fixture
    child_process_label: str = 'CalculationNodeWithIO',  # Assumed label for the IO calcs
    # Assume standard link labels used by the fixture
    wc_to_sub_link_label: str = 'sub_workflow',
    sub_to_calc_link_label: str = 'calculation',
) -> Dict[str, List[Any]]:
    """
    Generates the expected dump tree for the test nested WorkChain with IO children.
    Assumes wc_node calls wc_node_sub, which calls the two calculation nodes.
    Uses numerical prefixes based on observed dumper behavior.
    Uses content definition appropriate for whether outputs were attached.
    Uses correct nested directory naming convention: {prefix}-{link_label}-{child_pk}.
    """
    # Top-level directory name uses label and PK
    wc_node_dir_name = f'{wc_process_label}-{wc_pk}'

    # Content for children remains the same
    child1_content = _IO_CALC_NODE_CONTENT_NESTED_NO_OUTPUTS
    child2_content = _IO_CALC_NODE_CONTENT_NESTED_NO_OUTPUTS

    # Build the sub-workflow's content, nesting the calculations
    wc_sub_content = [
        '.aiida_dump_safeguard',
        'aiida_node_metadata.yaml',
        # Assuming calculations are called in sequence (01-, 02-)
        {f'01-{sub_to_calc_link_label}-{child_calc_pks[0]}': child1_content},  # Nested child 1 dir key uses PK
        {f'02-{sub_to_calc_link_label}-{child_calc_pks[1]}': child2_content},  # Nested child 2 dir key uses PK
    ]

    # Build the main workflow's content, nesting the sub-workflow
    # Key now uses: {prefix}-{link_label}-{CHILD_PK}
    wc_content = [
        '.aiida_dump_safeguard',
        'aiida_node_metadata.yaml',
        # Assuming sub-workflow is the first thing called (01-)
        {f'01-{wc_to_sub_link_label}-{wc_sub_pk}': wc_sub_content},  # Nested sub-workflow dir key uses PK
    ]

    return {wc_node_dir_name: wc_content}


# --- Dynamic Archive Assembly Helpers ---
def _assemble_nodes_by_type(node_trees: List[Dict]) -> Dict[str, List[Dict]]:
    """Helper to group node tree dicts by type."""
    grouped_by_type: Dict[str, List[Dict]] = {
        'calculations': [],
        'workflows': [],
        'misc': [],
    }
    for node_tree in node_trees:
        node_key = next(iter((node_tree.keys())))

        if 'Calculation' in node_key or 'multiply' in node_key:
            grouped_by_type['calculations'].append(node_tree)
        elif 'WorkChain' in node_key:  # Keywords for workflows/functions
            grouped_by_type['workflows'].append(node_tree)
        else:
            grouped_by_type['misc'].append(node_tree)  # Fallback category
    # Remove empty categories
    return {k: v for k, v in grouped_by_type.items() if v}


def get_expected_profile_dump_tree(
    groups_data: Optional[Dict[str, List[Dict]]] = None,
    ungrouped_data: Optional[List[Dict]] = None,
    organize_by_groups: bool = True,
) -> Dict[str, List[Any]]:
    """
    Generates the expected profile dump tree structure dynamically.

    Args:
        groups_data: Dict mapping group_label to list of node tree dicts for that group.
                     Example: {'add-group': [calc_tree1], 'multiply-add-group': [wc_tree1]}
        ungrouped_data: List of node tree dicts for ungrouped nodes.
        organize_by_groups: If True, nests nodes under group dirs/type subdirs.
                            If False, places all nodes directly under top-level type dirs.

    Returns:
        A dictionary representing the expected file/directory tree structure.
    """
    top_level_content = [
        'aiida_dump_log.json',
        '.aiida_dump_safeguard',
    ]

    if organize_by_groups:
        group_entries = []
        if groups_data:
            for label, node_trees in groups_data.items():
                grouped_nodes_by_type = _assemble_nodes_by_type(node_trees)
                group_content = ['.aiida_dump_safeguard']  # Safeguard inside each group dir

                # Iterate through the assembled types and add a dictionary for each
                for type_label, trees in grouped_nodes_by_type.items():
                    # No need to check for emptiness again, _assemble_nodes_by_type did it
                    group_content.append({type_label: trees})  # Append {'calculations': [...]} etc.

                group_entries.append({label: group_content})

        if group_entries:
            top_level_content.append({'groups': group_entries})

        if ungrouped_data:
            ungrouped_nodes_by_type = _assemble_nodes_by_type(ungrouped_data)
            # Check if there's actually anything to add for the 'ungrouped' directory
            if ungrouped_nodes_by_type:
                ungrouped_entry = ['.aiida_dump_safeguard']  # Safeguard for ungrouped dir
                for type_label, trees in ungrouped_nodes_by_type.items():
                    # No need to check for emptiness again
                    ungrouped_entry.append({type_label: trees})
                top_level_content.append({'ungrouped': ungrouped_entry})

    else:  # Not organized by groups (flat structure at top level by type)
        all_node_trees = []
        if groups_data:
            for node_list in groups_data.values():
                all_node_trees.extend(node_list)
        # If also_ungrouped=True was used to generate the list, they are already included.
        # If only specific groups were selected but ungrouped=True, they might be passed here.
        if ungrouped_data:
            all_node_trees.extend(ungrouped_data)

        nodes_by_type = _assemble_nodes_by_type(all_node_trees)

        # Add top-level directories for each node type
        for type_label, trees in nodes_by_type.items():
            # No need to check for emptiness again
            top_level_content.append({type_label: trees})

    return {profile_dump_label: top_level_content}


def get_expected_group_dump_tree(dump_label: str, node_trees: List[Dict]) -> Dict[str, List[Any]]:
    """Generates the expected tree for the output of a group dump."""
    content = [
        'aiida_dump_log.json',
        '.aiida_dump_safeguard',
    ]
    nodes_by_type = _assemble_nodes_by_type(node_trees)

    # Iterate through the sorted types and append a dictionary for each subdirectory
    for type_label, trees in nodes_by_type.items():
        # The value 'trees' is already the list of node dictionaries [{node1: content}, {node2: content}]
        content.append({type_label: trees})

    return {dump_label: content}


class TestProcessDumping:
    """Tests the dumping of process nodes."""

    # test_init_and_verify: Remains largely the same, uses node.pk/uuid/process_label
    # test_from_config: Remains the same, tests config loading
    # test_dump_unsealed_raises: Remains the same
    # test_dump_unsealed_allowed: Remains the same

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_facade_wc_io(self, generate_calculation_node_io, generate_workchain_node_io, tmp_path):
        """Test dumping WorkChain with nested IO files."""
        # Setup
        cj_nodes = [
            generate_calculation_node_io(attach_outputs=False),
            generate_calculation_node_io(attach_outputs=False),
        ]
        wc_node = generate_workchain_node_io(cj_nodes=cj_nodes)  # Fixture seals and stores
        wc_pk = wc_node.pk
        wc_process_label = wc_node.process_label or 'WorkflowNode'  # Get actual label or default

        # --- Get PKs of the nested structure ---
        called_workflows = wc_node.called  # Should contain wc_node_sub
        assert len(called_workflows) == 1, 'Expected one called sub-workflow'
        wc_node_sub = called_workflows[0]
        wc_sub_pk = wc_node_sub.pk
        wc_sub_process_label = wc_node_sub.process_label or 'WorkflowNode'

        called_calcs = wc_node_sub.called  # Calcs called by the sub-workflow
        assert len(called_calcs) == 2, 'Expected two called calculations from sub-workflow'
        # Sort PKs for consistent order
        child_calc_pks = tuple(sorted([n.pk for n in called_calcs]))
        # Get label from one of the children (assuming they are the same type)
        child_process_label = called_calcs[0].process_label or 'CalculationNodeWithIO'
        # --- End PK gathering ---

        # --- Generate the expected tree using the CORRECT helper ---
        expected_wc_content_tree = get_expected_nested_io_wc_tree(
            wc_pk=wc_pk,
            wc_sub_pk=wc_sub_pk,
            child_calc_pks=child_calc_pks,
            wc_process_label=wc_process_label,
            wc_sub_process_label=wc_sub_process_label,
            child_process_label=child_process_label,
        )
        # --- End dynamic generation ---

        dump_label = f'{wc_process_label}-{wc_pk}'
        dump_target_path = tmp_path / dump_label
        config = DumpConfig(dump_mode=DumpMode.OVERWRITE)

        wc_node.dump(config=config, output_path=dump_target_path)

        # Create the final expected structure including standard files
        expected_tree_content = expected_wc_content_tree[dump_label]
        expected_tree_final = {
            dump_label: [
                'README.md',
                'aiida_dump_log.json',
            ]
            + expected_tree_content  # Add standard files to node content list
        }

        compare_tree(expected=expected_tree_final, base_path=tmp_path)
        assert (dump_target_path / 'README.md').is_file()
        assert (dump_target_path / 'aiida_dump_log.json').is_file()

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_facade_multiply_add(self, tmp_path, generate_workchain_multiply_add):
        """Test dumping MultiplyAddWorkChain using (nested and flat)."""

        wc_node = generate_workchain_multiply_add()
        wc_pk = wc_node.pk
        child_pks = tuple(sorted([n.pk for n in wc_node.called_descendants]))
        assert len(child_pks) == 2
        dump_label = f'{wc_node.process_label}-{wc_pk}'

        # --- Nested Dump ---
        dump_target_path_nested = tmp_path / dump_label
        config_nested = DumpConfig(dump_mode=DumpMode.OVERWRITE, include_outputs=True)  # Include outputs

        wc_node.dump(config=config_nested, output_path=dump_target_path_nested)

        # Generate expected nested tree
        expected_wc_content_tree = get_expected_multiply_add_wc_tree(wc_pk=wc_pk, child_pks=child_pks)
        expected_tree_content_nested = expected_wc_content_tree[dump_label]
        expected_tree_nested = {
            dump_label: [
                'README.md',
                'aiida_dump_log.json',
                '.aiida_dump_safeguard',
            ]
            + expected_tree_content_nested
        }
        compare_tree(expected=expected_tree_nested, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_facade_calculation_io(self, tmp_path, generate_calculation_node_io):
        """Test dumping a CalculationNode with complex IO."""
        calculation_node = generate_calculation_node_io(attach_outputs=True)
        calculation_node.seal()
        calc_pk = calculation_node.pk
        # Try to get a more specific label if possible from fixture, else use generic
        process_label = getattr(calculation_node, 'process_label', 'CalculationNodeWithIO')
        dump_label = f'{process_label}-{calc_pk}'
        dump_target_path = tmp_path / dump_label

        config = DumpConfig(include_outputs=True, dump_mode=DumpMode.OVERWRITE)
        calculation_node.dump(config=config, output_path=dump_target_path)

        # Generate expected tree
        expected_node_tree = get_expected_io_calc_tree(pk=calc_pk, process_label=process_label)
        expected_tree_content = expected_node_tree[dump_label]
        expected_tree = {
            dump_label: [
                'README.md',
                'aiida_dump_log.json',
                '.aiida_dump_safeguard',
            ]
            + expected_tree_content
        }
        compare_tree(expected=expected_tree, base_path=tmp_path)

        # Content checks remain valuable
        file_path = dump_target_path / 'inputs' / 'file.txt'
        assert file_path.read_text() == 'a'
        node_input_path = dump_target_path / 'node_inputs' / 'singlefile' / 'file.txt'
        assert node_input_path.read_text() == 'a'
        node_output_path = dump_target_path / 'node_outputs' / 'singlefile' / 'file.txt'
        assert node_output_path.read_text() == 'a'  # Assuming output is same as input for this test node

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_facade_calculation_flat(self, tmp_path, generate_calculation_node_io):
        """Test flat dumping of a CalculationNode."""
        # As noted before, the exact flat structure representation and verification
        # using compare_tree is tricky and potentially fragile.
        # Content verification (checking file existence/content at the top level)
        # or dump/import testing might be more suitable for flat dumps.
        # Skipping the compare_tree part for flat dump here.
        calculation_node = generate_calculation_node_io(attach_outputs=True)
        calculation_node.seal()
        calc_pk = calculation_node.pk
        process_label = getattr(calculation_node, 'process_label', 'CalculationNodeWithIO')
        dump_label = f'{process_label}-{calc_pk}-flat'  # Use different name
        dump_target_path = tmp_path / dump_label

        config = DumpConfig(flat=True, include_outputs=True, dump_mode=DumpMode.OVERWRITE)

        calculation_node.dump(config=config, output_path=dump_target_path)

        # Perform basic checks instead of full compare_tree for flat dump
        assert (dump_target_path / 'aiida_node_metadata.yaml').is_file()
        assert (dump_target_path / 'aiida_dump_log.json').is_file()
        assert (dump_target_path / 'file.txt').is_file()  # Check a key file is flattened
        assert (dump_target_path / 'default.npy').is_file()
        # Add more specific checks if needed based on expected flat output

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_facade_calculation_add(self, tmp_path, generate_calculation_node_add):
        """Test dumping ArithmeticAddCalculation."""
        calculation_node = generate_calculation_node_add()  # Fixture runs and seals
        calc_pk = calculation_node.pk
        process_label = calculation_node.process_label
        dump_label = f'{process_label}-{calc_pk}'
        dump_target_path = tmp_path / dump_label

        config = DumpConfig(include_outputs=True, dump_mode=DumpMode.OVERWRITE)

        calculation_node.dump(config=config, output_path=dump_target_path)

        # Generate expected tree using the node helper's content
        expected_node_content = get_expected_add_calc_tree(pk=calc_pk)[dump_label]
        expected_tree = {
            dump_label: [
                'README.md',
                'aiida_dump_log.json',
                '.aiida_dump_safeguard',
            ]
            + expected_node_content
        }
        compare_tree(expected=expected_tree, base_path=tmp_path)


class TestGroupDumping:
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_group(self, tmp_path, setup_add_group):
        add_group = setup_add_group
        assert len(add_group.nodes) == 1
        node_pk = add_group.nodes[0].pk

        # Generate node tree
        calc_tree = get_expected_add_calc_tree(pk=node_pk)
        # Assemble group tree
        expected_tree = get_expected_group_dump_tree(dump_label=add_group_label, node_trees=[calc_tree])

        output_path = tmp_path / add_group_label
        config = DumpConfig()
        add_group.dump(config=config, output_path=output_path)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_multiply_add_group(self, tmp_path, setup_multiply_add_group):
        multiply_add_group = setup_multiply_add_group
        assert len(multiply_add_group.nodes) == 1
        wc_node = multiply_add_group.nodes[0]
        wc_pk = wc_node.pk
        child_pks = tuple(sorted([n.pk for n in wc_node.called_descendants]))
        assert len(child_pks) == 2

        # Generate node tree
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=wc_pk, child_pks=child_pks)
        # Assemble group tree
        expected_tree = get_expected_group_dump_tree(dump_label=multiply_add_group_label, node_trees=[wc_tree])

        output_path = tmp_path / multiply_add_group_label
        # Rely on default config for incremental filter_by_last_dump_time=True
        multiply_add_group.dump(output_path=output_path)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_node_to_group(self, tmp_path, setup_add_group, generate_calculation_node_add):
        add_group = setup_add_group
        node1 = add_group.nodes[0]
        node2 = generate_calculation_node_add()

        output_path = tmp_path / add_group_label
        add_group.dump(output_path=output_path)

        # Dump 1: Only node1
        tree1 = get_expected_group_dump_tree(
            dump_label=add_group_label,
            node_trees=[get_expected_add_calc_tree(node1.pk)],
        )
        compare_tree(expected=tree1, base_path=tmp_path)

        # Add node2 to the group
        add_group.add_nodes([node2])

        # Dump 2: Both nodes
        add_group.dump(output_path=output_path)

        tree2 = get_expected_group_dump_tree(
            dump_label=add_group_label,
            node_trees=[
                get_expected_add_calc_tree(node1.pk),
                get_expected_add_calc_tree(node2.pk),
            ],
        )
        compare_tree(expected=tree2, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_group_copy(self, tmp_path, setup_add_group):
        add_group = setup_add_group
        node1 = add_group.nodes[0]
        copy_label = 'add-group-copy'
        copy_dump_label = f'{copy_label}-dump'
        dest_group, _ = orm.Group.collection.get_or_create(label=copy_label)
        dest_group.add_nodes(list(add_group.nodes))

        output_path = tmp_path / copy_dump_label
        config = DumpConfig(filter_by_last_dump_time=False)
        dest_group.dump(config=config, output_path=output_path)

        # Generate expected tree for the copied group dump
        calc_tree = get_expected_add_calc_tree(pk=node1.pk)
        expected_tree = get_expected_group_dump_tree(dump_label=copy_dump_label, node_trees=[calc_tree])
        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_sub_calc_group(self, tmp_path, generate_workchain_multiply_add):
        """Test dumping a group containing only sub-calculations of a workflow."""
        wf_node = generate_workchain_multiply_add()
        sub_calcs = list(wf_node.called_descendants)
        assert len(sub_calcs) == 2
        multiply_child = next(n for n in sub_calcs if 'multiply' in n.process_label)
        add_child = next(n for n in sub_calcs if 'ArithmeticAdd' in n.process_label)

        group_label = 'sub-calc-group'
        dump_label = f'{group_label}-dump'
        group, _ = orm.Group.collection.get_or_create(label=group_label)
        group.add_nodes(sub_calcs)

        output_path = tmp_path / dump_label
        config = DumpConfig(filter_by_last_dump_time=False)
        group.dump(config=config, output_path=output_path)

        # Generate expected tree for the group containing sub-calcs
        multiply_tree = get_expected_multiply_func_tree(pk=multiply_child.pk)
        add_tree = get_expected_add_calc_tree(pk=add_child.pk)
        expected_tree = get_expected_group_dump_tree(dump_label=dump_label, node_trees=[multiply_tree, add_tree])
        compare_tree(expected=expected_tree, base_path=tmp_path)


class TestProfileDumping:
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_group(self, tmp_path, setup_add_group):
        add_group = setup_add_group
        assert len(add_group.nodes) == 1
        add_node_pk = add_group.nodes[0].pk

        # Generate node tree
        calc_tree = get_expected_add_calc_tree(pk=add_node_pk)
        # Assemble profile tree
        expected_tree = get_expected_profile_dump_tree(groups_data={add_group.label: [calc_tree]})

        config = DumpConfig(all_entries=True)

        profile = load_profile()
        profile.dump(config=config, output_path=tmp_path / profile_dump_label)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_multiply_add_group(self, tmp_path, setup_multiply_add_group):
        multiply_add_group = setup_multiply_add_group
        assert len(multiply_add_group.nodes) == 1
        wc_node = multiply_add_group.nodes[0]
        wc_pk = wc_node.pk
        child_pks = tuple(sorted([_.pk for _ in wc_node.called_descendants]))  # Ensure consistent order
        assert len(child_pks) == 2, 'Expected 2 children for WC'

        # Generate node tree
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=wc_pk, child_pks=child_pks)
        # Assemble profile tree
        expected_tree = get_expected_profile_dump_tree(groups_data={multiply_add_group.label: [wc_tree]})

        profile = load_profile()
        config = DumpConfig(all_entries=True)
        profile.dump(config=config, output_path=tmp_path / profile_dump_label)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_multiply_add_groups(self, tmp_path, setup_add_group, setup_multiply_add_group):
        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group

        # Get PKs
        assert len(add_group.nodes) == 1
        add_node_pk = add_group.nodes[0].pk
        assert len(multiply_add_group.nodes) == 1
        wc_node = multiply_add_group.nodes[0]
        wc_pk = wc_node.pk
        child_pks = tuple(sorted([_.pk for _ in wc_node.called_descendants]))
        assert len(child_pks) == 2

        # Generate individual node trees
        calc_tree = get_expected_add_calc_tree(pk=add_node_pk)
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=wc_pk, child_pks=child_pks)

        # Assemble profile tree
        expected_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [calc_tree],
                multiply_add_group.label: [wc_tree],
            }
        )

        profile = load_profile()
        config = DumpConfig(all_entries=True)
        profile.dump(config=config, output_path=tmp_path / profile_dump_label)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_multiply_add_add_groups(self, tmp_path, setup_add_group, setup_multiply_add_group):
        # This test setup is identical to the previous one, just run in a different order
        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group
        assert len(add_group.nodes) == 1
        add_node_pk = add_group.nodes[0].pk
        assert len(multiply_add_group.nodes) == 1
        wc_node = multiply_add_group.nodes[0]
        wc_pk = wc_node.pk
        child_pks = tuple(sorted([_.pk for _ in wc_node.called_descendants]))
        assert len(child_pks) == 2

        calc_tree = get_expected_add_calc_tree(pk=add_node_pk)
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=wc_pk, child_pks=child_pks)

        # Assemble profile tree (order of groups in dict doesn't matter for structure)
        expected_tree = get_expected_profile_dump_tree(
            groups_data={
                multiply_add_group.label: [wc_tree],  # Different order here
                add_group.label: [calc_tree],
            }
        )

        profile = load_profile()
        config = DumpConfig(all_entries=True)
        profile.dump(config=config, output_path=tmp_path / profile_dump_label)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_no_organize_by_groups(self, tmp_path, setup_add_group, setup_multiply_add_group):
        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group
        assert len(add_group.nodes) == 1
        add_node_pk = add_group.nodes[0].pk
        assert len(multiply_add_group.nodes) == 1
        wc_node = multiply_add_group.nodes[0]
        wc_pk = wc_node.pk
        child_pks = tuple(sorted([_.pk for _ in wc_node.called_descendants]))
        assert len(child_pks) == 2

        # Generate node trees
        calc_tree = get_expected_add_calc_tree(pk=add_node_pk)
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=wc_pk, child_pks=child_pks)

        # Assemble profile tree NOT organized by groups
        expected_tree = get_expected_profile_dump_tree(
            groups_data={  # Need to pass groups so nodes are selected
                add_group.label: [calc_tree],
                multiply_add_group.label: [wc_tree],
            },
            organize_by_groups=False,
        )

        profile = load_profile()
        config = DumpConfig(all_entries=True, organize_by_groups=False)
        profile.dump(output_path=tmp_path / profile_dump_label, config=config)

        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_also_ungrouped(
        self,
        tmp_path,
        setup_add_group,
        setup_multiply_add_group,
        generate_calculation_node_add,
        generate_workchain_multiply_add,
    ):
        """Tests dumping grouped and optionally ungrouped nodes."""
        # Setup grouped nodes
        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group
        grouped_add_node = add_group.nodes[0]
        grouped_wc_node = multiply_add_group.nodes[0]
        grouped_wc_child_pks = tuple(sorted([n.pk for n in grouped_wc_node.called_descendants]))

        # Create ungrouped nodes
        ungrouped_add_node = generate_calculation_node_add()
        ungrouped_wc_node = generate_workchain_multiply_add()
        ungrouped_wc_child_pks = tuple(sorted([n.pk for n in ungrouped_wc_node.called_descendants]))

        output_path = tmp_path / profile_dump_label

        # --- Dump 1: Only grouped nodes ---
        config_grouped = DumpConfig(all_entries=True, also_ungrouped=False)
        profile = load_profile()
        profile.dump(output_path=output_path, config=config_grouped)

        # Generate expected tree for grouped nodes only
        grouped_calc_tree = get_expected_add_calc_tree(pk=grouped_add_node.pk)
        grouped_wc_tree = get_expected_multiply_add_wc_tree(wc_pk=grouped_wc_node.pk, child_pks=grouped_wc_child_pks)
        expected_tree_grouped = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [grouped_calc_tree],
                multiply_add_group.label: [grouped_wc_tree],
            },
            organize_by_groups=True,  # Assuming default organization
        )
        compare_tree(expected=expected_tree_grouped, base_path=tmp_path)

        # --- Dump 2: Include ungrouped nodes (incremental) ---
        # Note: We re-instantiate dumper to ensure fresh state reading if needed,
        # or rely on the dumper correctly handling incremental logic with config change.
        # Re-instantiating is often safer in tests.
        config_all = DumpConfig(
            all_entries=True,
            also_ungrouped=True,
            filter_by_last_dump_time=False,
            dump_mode=DumpMode.INCREMENTAL,
        )
        profile = load_profile()
        profile.dump(output_path=output_path, config=config_all)

        # Generate expected tree for all nodes
        ungrouped_calc_tree = get_expected_add_calc_tree(pk=ungrouped_add_node.pk)
        ungrouped_wc_tree = get_expected_multiply_add_wc_tree(
            wc_pk=ungrouped_wc_node.pk, child_pks=ungrouped_wc_child_pks
        )
        expected_tree_all = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [grouped_calc_tree],
                multiply_add_group.label: [grouped_wc_tree],
            },
            ungrouped_data=[ungrouped_calc_tree, ungrouped_wc_tree],
            organize_by_groups=True,
        )
        compare_tree(expected=expected_tree_all, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_node_to_group(self, tmp_path, setup_add_group, generate_calculation_node_add):
        add_group = setup_add_group
        node1 = add_group.nodes[0]
        node2 = generate_calculation_node_add()  # Created but not in group yet

        output_path = tmp_path / profile_dump_label
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)
        profile = load_profile()

        # Dump 1: Only node1 should be in the group dump
        profile.dump(output_path=output_path, config=config)
        tree1 = get_expected_profile_dump_tree(groups_data={add_group.label: [get_expected_add_calc_tree(node1.pk)]})
        compare_tree(expected=tree1, base_path=tmp_path)

        # Add node2 to the group
        add_group.add_nodes([node2])

        # Dump 2: Both nodes should be in the group dump
        # Re-run dump, should pick up group change
        profile.dump(output_path=output_path, config=config)
        tree2 = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [
                    get_expected_add_calc_tree(node1.pk),
                    get_expected_add_calc_tree(node2.pk),
                ]
            }
        )
        compare_tree(expected=tree2, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_group_copy(self, tmp_path, setup_add_group):
        add_group = setup_add_group
        node1 = add_group.nodes[0]
        copy_group_label = 'add-group-copy'
        dest_group, _ = orm.Group.collection.get_or_create(label=copy_group_label)
        dest_group.add_nodes(list(add_group.nodes))

        output_path = tmp_path / profile_dump_label

        profile = load_profile()
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)
        profile.dump(output_path=output_path, config=config)

        # Generate expected tree with node1 in both groups
        calc_tree = get_expected_add_calc_tree(pk=node1.pk)
        expected_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [calc_tree],
                copy_group_label: [calc_tree],  # Node appears in both
            }
        )
        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_group_copy_symlink(self, tmp_path, setup_add_group):
        add_group = setup_add_group
        node1 = add_group.nodes[0]
        copy_group_label = 'add-group-copy'
        dest_group, _ = orm.Group.collection.get_or_create(label=copy_group_label)
        dest_group.add_nodes(list(add_group.nodes))

        output_path = tmp_path / profile_dump_label
        config = DumpConfig(all_entries=True, symlink_calcs=True, filter_by_last_dump_time=False)
        profile = load_profile()
        profile.dump(output_path=output_path, config=config)

        # --- Symlink specific checks ---
        node_dir_name = f'{node1.process_label}-{node1.pk}'
        path_in_group1 = output_path / 'groups' / add_group.label / 'calculations' / node_dir_name
        path_in_group2 = output_path / 'groups' / copy_group_label / 'calculations' / node_dir_name

        assert path_in_group1.is_dir() and not path_in_group1.is_symlink(), 'Source path should be a directory'
        assert path_in_group2.is_symlink(), 'Second path should be a symlink'
        assert path_in_group2.resolve() == path_in_group1.resolve(), 'Symlink target mismatch'
        # --- End symlink checks ---

        # Check overall structure (compare_tree implicitly follows links)
        calc_tree = get_expected_add_calc_tree(pk=node1.pk)
        expected_tree = get_expected_profile_dump_tree(
            groups_data={add_group.label: [calc_tree], copy_group_label: [calc_tree]}
        )
        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_sub_calc_group(self, tmp_path, generate_workchain_multiply_add):
        """Test dumping a group containing only sub-calculations of a workflow."""
        wf_node = generate_workchain_multiply_add()
        sub_calcs = list(wf_node.called_descendants)
        assert len(sub_calcs) == 2
        multiply_child = next(n for n in sub_calcs if 'multiply' in n.process_label)
        add_child = next(n for n in sub_calcs if 'ArithmeticAdd' in n.process_label)

        group_label = 'sub-calc-group'
        group, _ = orm.Group.collection.get_or_create(label=group_label)
        group.add_nodes(sub_calcs)

        output_path = tmp_path / profile_dump_label

        profile = load_profile()
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)
        profile.dump(output_path=output_path, config=config)

        # Generate expected tree (only sub-calcs in the group)
        multiply_tree = get_expected_multiply_func_tree(pk=multiply_child.pk)
        add_tree = get_expected_add_calc_tree(pk=add_child.pk)
        expected_tree = get_expected_profile_dump_tree(groups_data={group_label: [multiply_tree, add_tree]})
        compare_tree(expected=expected_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_delete_nodes(self, tmp_path, setup_add_group, setup_multiply_add_group):
        from aiida.tools.graph.deletions import delete_nodes

        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group
        node_add = add_group.nodes[0]
        node_wc = multiply_add_group.nodes[0]
        wc_child_pks = tuple(sorted([n.pk for n in node_wc.called_descendants]))

        # === Store info needed AFTER deletion BEFORE deleting ===
        deleted_node_pk = node_add.pk
        deleted_node_process_label = node_add.process_label
        # ======================================================

        output_path = tmp_path / profile_dump_label

        profile = load_profile()
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)

        # Dump 1: Full initial state
        profile.dump(output_path=output_path, config=config)
        calc_tree = get_expected_add_calc_tree(pk=node_add.pk)  # Getting pk here is fine
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=node_wc.pk, child_pks=wc_child_pks)
        initial_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [calc_tree],
                multiply_add_group.label: [wc_tree],
            }
        )
        compare_tree(expected=initial_tree, base_path=tmp_path)

        # Delete the add node
        delete_nodes(pks=[node_add.pk], dry_run=False)  # Using pk is fine

        # Dump 2: Incremental dump with delete_missing=True
        config_del = DumpConfig(delete_missing=True, all_entries=True, dump_mode=DumpMode.INCREMENTAL)
        profile.dump(output_path=output_path, config=config_del)

        # Generate expected tree after deletion
        final_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [],  # Empty node list
                multiply_add_group.label: [wc_tree],  # wc_tree definition is still valid
            }
        )
        compare_tree(expected=final_tree, base_path=tmp_path)

        # Explicitly check the deleted node's directory is gone
        # === Use the stored values ===
        deleted_node_dir = (
            output_path
            / 'groups'
            / add_group.label
            / 'calculations'
            / f'{deleted_node_process_label}-{deleted_node_pk}'
        )
        # ============================
        assert not deleted_node_dir.exists(), 'Deleted node directory still exists'

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_delete_group(self, tmp_path, setup_add_group, setup_multiply_add_group):
        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group
        node_add = add_group.nodes[0]
        node_wc = multiply_add_group.nodes[0]
        wc_child_pks = tuple(sorted([n.pk for n in node_wc.called_descendants]))

        output_path = tmp_path / profile_dump_label

        profile = load_profile()
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)

        # Dump 1: Full initial state
        profile.dump(output_path=output_path, config=config)
        calc_tree_initial = get_expected_add_calc_tree(pk=node_add.pk)
        wc_tree_initial = get_expected_multiply_add_wc_tree(wc_pk=node_wc.pk, child_pks=wc_child_pks)
        initial_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [calc_tree_initial],
                multiply_add_group.label: [wc_tree_initial],
            }
        )
        compare_tree(expected=initial_tree, base_path=tmp_path)

        # Delete the multiply_add_group (but not its nodes)
        orm.Group.collection.delete(multiply_add_group.pk)

        # Dump 2: Incremental dump, should remove multiply_add_group dir
        config_del = DumpConfig(delete_missing=True, all_entries=True, dump_mode=DumpMode.INCREMENTAL)
        profile.dump(output_path=output_path, config=config_del)

        # Generate expected tree after group deletion
        tree_after_del = get_expected_profile_dump_tree(
            groups_data={add_group.label: [calc_tree_initial]}  # Only add_group remains
        )
        compare_tree(expected=tree_after_del, base_path=tmp_path)
        # Check multiply_add_group dir is gone
        assert not (output_path / 'groups' / multiply_add_group_label).exists()

        # Dump 3: Include ungrouped, should find the WC node now
        config_ungrouped = DumpConfig(
            also_ungrouped=True,
            delete_missing=True,
            all_entries=True,
            dump_mode=DumpMode.INCREMENTAL,
            filter_by_last_dump_time=False,
        )
        profile.dump(output_path=output_path, config=config_ungrouped)

        # Generate expected tree with WC node in ungrouped
        tree_final = get_expected_profile_dump_tree(
            groups_data={add_group.label: [calc_tree_initial]},
            ungrouped_data=[wc_tree_initial],  # WC tree now appears here
        )
        compare_tree(expected=tree_final, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_node_group_membership_change(self, tmp_path, setup_add_group, setup_multiply_add_group):
        add_group = setup_add_group
        multiply_add_group = setup_multiply_add_group
        node_add = add_group.nodes[0]
        node_wc = multiply_add_group.nodes[0]
        wc_child_pks = tuple(sorted([n.pk for n in node_wc.called_descendants]))

        output_path = tmp_path / profile_dump_label
        profile = load_profile()
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)

        # Dump 1: Initial state
        profile.dump(config=config, output_path=output_path)
        calc_tree = get_expected_add_calc_tree(pk=node_add.pk)
        wc_tree = get_expected_multiply_add_wc_tree(wc_pk=node_wc.pk, child_pks=wc_child_pks)
        initial_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [calc_tree],
                multiply_add_group.label: [wc_tree],
            }
        )
        compare_tree(expected=initial_tree, base_path=tmp_path)

        # Change membership
        add_group.remove_nodes([node_add])
        multiply_add_group.add_nodes([node_add])

        # Dump 2: Should reflect the change
        profile.dump(config=config, output_path=output_path)
        final_tree = get_expected_profile_dump_tree(
            groups_data={
                add_group.label: [],  # Now empty
                multiply_add_group.label: [wc_tree, calc_tree],  # Contains both now
            }
        )
        compare_tree(expected=final_tree, base_path=tmp_path)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_add_group_relabel(self, tmp_path, setup_add_group):
        add_group = setup_add_group
        node_add = add_group.nodes[0]
        old_label = add_group.label
        new_label = 'add-group-relabelled'

        output_path = tmp_path / profile_dump_label
        config = DumpConfig(all_entries=True, filter_by_last_dump_time=False)
        profile = load_profile()

        # Dump 1: Initial state
        profile.dump(config=config, output_path=output_path)
        calc_tree = get_expected_add_calc_tree(pk=node_add.pk)
        initial_tree = get_expected_profile_dump_tree(groups_data={old_label: [calc_tree]})
        compare_tree(expected=initial_tree, base_path=tmp_path)

        # Relabel the group
        add_group.label = new_label

        # Dump 2: Update groups, should reflect relabeling
        # Re-instantiate dumper or ensure config update is picked up
        config_update = DumpConfig(
            all_entries=True,
            relabel_groups=True,
            dump_mode=DumpMode.INCREMENTAL,
            filter_by_last_dump_time=False,
        )
        profile.dump(config=config_update, output_path=output_path)

        # Generate expected tree with new label
        final_tree = get_expected_profile_dump_tree(groups_data={new_label: [calc_tree]})
        compare_tree(expected=final_tree, base_path=tmp_path)

        # Verify old group directory is gone (assuming dumper removes it on relabel+update)
        assert not (output_path / 'groups' / old_label).exists()

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_no_changes_early_return(self, tmp_path, setup_add_group, caplog):
        """Tests that the dumper returns early if no changes are detected."""
        add_group = setup_add_group
        node_add = add_group.nodes[0]

        output_path = tmp_path / profile_dump_label
        profile = load_profile()
        config = DumpConfig(all_entries=True)

        # Dump 1: Initial dump
        profile.dump(output_path=output_path, config=config)
        initial_tree = get_expected_profile_dump_tree(
            groups_data={add_group.label: [get_expected_add_calc_tree(node_add.pk)]}
        )
        compare_tree(expected=initial_tree, base_path=tmp_path)

        # Dump 2: No changes, check log message
        caplog.clear()
        with caplog.at_level(logging.REPORT, logger='aiida.tools.dumping.engine'):
            profile.dump(output_path=output_path, config=config)  # Should detect no changes via log

        assert (
            'No changes detected since last dump' in caplog.text
        ), "Engine did not log the expected 'No changes detected' message."
        compare_tree(expected=initial_tree, base_path=tmp_path)  # Structure remains identical

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_filter_by_last_dump_time(self, tmp_path, setup_add_group, generate_calculation_node_add):
        """Tests that unmodified nodes are skipped in incremental dumps."""
        add_group = setup_add_group
        original_node = add_group.nodes[0]
        output_path = tmp_path / profile_dump_label
        config = DumpConfig(
            all_entries=True,
            filter_by_last_dump_time=True,  # Explicitly enable (though default)
            dump_mode=DumpMode.INCREMENTAL,  # Essential for this test
        )
        profile = load_profile()

        # Dump 1: Initial dump
        profile.dump(output_path=output_path, config=config)
        original_calc_tree = get_expected_add_calc_tree(pk=original_node.pk)
        initial_tree = get_expected_profile_dump_tree(groups_data={add_group.label: [original_calc_tree]})
        compare_tree(expected=initial_tree, base_path=tmp_path)

        # Record mtime
        original_node_dir_name = f'{original_node.process_label}-{original_node.pk}'
        original_node_dump_path = output_path / 'groups' / add_group.label / 'calculations' / original_node_dir_name
        assert original_node_dump_path.exists()
        mtime_orig_node_before = original_node_dump_path.stat().st_mtime
        time.sleep(0.1)  # Ensure timestamp changes

        # Add a new node
        new_node = generate_calculation_node_add()
        add_group.add_nodes([new_node])

        # Dump 2: Incremental dump, filtering by time
        profile.dump(output_path=output_path, config=config)

        # Check mtime of original node dir DID NOT change
        mtime_orig_node_after = original_node_dump_path.stat().st_mtime
        # Use approx comparison due to potential filesystem time resolution issues
        assert (
            abs(mtime_orig_node_before - mtime_orig_node_after) < 0.1
        ), 'Original node dump directory was modified in time-filtered incremental update'

        # Check new node dir DOES exist
        new_node_dir_name = f'{new_node.process_label}-{new_node.pk}'
        new_node_dump_path = output_path / 'groups' / add_group.label / 'calculations' / new_node_dir_name
        assert new_node_dump_path.is_dir(), 'New node was not dumped'

        # Verify final overall structure contains both
        new_calc_tree = get_expected_add_calc_tree(pk=new_node.pk)
        final_expected_tree = get_expected_profile_dump_tree(
            groups_data={add_group.label: [original_calc_tree, new_calc_tree]}
        )
        compare_tree(expected=final_expected_tree, base_path=tmp_path)

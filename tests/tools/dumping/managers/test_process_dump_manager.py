###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from pathlib import Path

import pytest
import yaml

from aiida import orm
from aiida.common.links import LinkType
from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.managers.process import NodeRepoIoDumper, WorkflowWalker


@pytest.mark.usefixtures('aiida_profile_clean')
class TestProcessDumpManager:
    """Tests the ProcessDumpManager logic."""

    def test_dump_calculation_content(self, process_dump_manager, generate_calculation_node_io, tmp_path):
        """Test the internal _dump_calculation_content method."""
        node = generate_calculation_node_io(attach_outputs=True)
        node.seal()
        dump_target_path = tmp_path / f'calc_dump_{node.pk}'
        dump_target_path.mkdir()  # Manager expects path to exist

        # Enable outputs for this test
        process_dump_manager.config.include_outputs = True
        process_dump_manager.repo_io_dumper._dump_calculation_content(node, dump_target_path)

        # Verify structure (similar to facade test, but focused on manager's output)
        assert (dump_target_path / 'inputs' / 'file.txt').is_file()
        assert (dump_target_path / 'node_inputs' / 'singlefile' / 'file.txt').is_file()
        assert (dump_target_path / 'node_outputs' / 'singlefile' / 'file.txt').is_file()
        # Check content
        assert (dump_target_path / 'inputs' / 'file.txt').read_text() == 'a'

    def test_dump_calculation_no_inputs(self, process_dump_manager, generate_calculation_node_io, tmp_path):
        """Test dumping calculation without inputs."""
        node = generate_calculation_node_io(attach_outputs=True)
        node.seal()
        dump_target_path = tmp_path / f'calc_dump_no_inputs_{node.pk}'
        dump_target_path.mkdir()

        process_dump_manager.config.include_inputs = False
        process_dump_manager.config.include_outputs = True  # Keep outputs
        process_dump_manager.repo_io_dumper._dump_calculation_content(node, dump_target_path)

        assert not (dump_target_path / 'node_inputs').exists()
        assert (dump_target_path / 'node_outputs').exists()
        assert (dump_target_path / 'inputs' / 'file.txt').is_file()  # Repo 'inputs' always dumped

    def test_dump_calculation_no_outputs(self, process_dump_manager, generate_calculation_node_io, tmp_path):
        """Test dumping calculation without outputs."""
        node = generate_calculation_node_io(attach_outputs=True)
        node.seal()
        dump_target_path = tmp_path / f'calc_dump_no_outputs_{node.pk}'
        dump_target_path.mkdir()

        process_dump_manager.config.include_inputs = True
        process_dump_manager.config.include_outputs = False
        process_dump_manager.repo_io_dumper._dump_calculation_content(node, dump_target_path)

        assert (dump_target_path / 'node_inputs').exists()
        assert not (dump_target_path / 'node_outputs').exists()
        assert not (dump_target_path / 'outputs').exists()  # 'retrieved' repo also skipped

    def test_generate_child_node_label(self, process_dump_manager, generate_workchain_multiply_add):
        """Test the child node label generation."""
        wc_node = generate_workchain_multiply_add()
        # Get outgoing links (assuming fixture creates them)
        called_links = wc_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
        called_links = sorted(called_links, key=lambda link_triple: link_triple.node.ctime)

        labels = [
            process_dump_manager._generate_child_node_label(idx, triple)
            for idx, triple in enumerate(called_links, start=1)
        ]
        # Example PKs will differ, check the structure
        assert labels[0].startswith('01-multiply-')
        assert labels[1].startswith('02-ArithmeticAddCalculation-')
        # Note: The fixture might create a 'result' node which isn't CALL_CALC/WORK
        # Adjust expectation based on actual fixture links

    def test_write_node_yaml(self, process_dump_manager, generate_calculation_node_add, tmp_path):
        """Test writing the node metadata YAML."""
        node = generate_calculation_node_add()
        dump_target_path = tmp_path / f'yaml_test_{node.pk}'
        dump_target_path.mkdir()

        process_dump_manager.metadata_writer._write(node, dump_target_path)
        yaml_path = dump_target_path / '.aiida_node_metadata.yaml'
        assert yaml_path.is_file()

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        assert 'Node data' in data
        assert 'User data' in data
        assert 'Computer data' in data
        assert 'Node attributes' in data
        assert 'Node extras' not in data

        # Test without attributes/extras
        process_dump_manager.config.include_attributes = False
        process_dump_manager.config.include_extras = False
        yaml_path.unlink()
        process_dump_manager.metadata_writer._write(node, dump_target_path)
        with open(yaml_path) as f:
            data_no_attr = yaml.safe_load(f)

        assert 'Node attributes' not in data_no_attr
        assert 'Node extras' not in data_no_attr

    def test_generate_readme(self, process_dump_manager, generate_workchain_multiply_add, tmp_path):
        """Test README generation."""
        node = generate_workchain_multiply_add()
        dump_target_path = tmp_path / f'readme_test_{node.pk}'
        dump_target_path.mkdir()

        process_dump_manager.readme_generator._generate(node, dump_target_path)
        readme_path = dump_target_path / 'README.md'
        assert readme_path.is_file()
        content = readme_path.read_text()

        assert f'AiiDA Process Dump: {node.process_label} <{node.pk}>' in content
        assert 'Process Status' in content
        assert 'Process Report' in content
        # assert 'Node Info' in content # Removed from manager for now
        assert 'ArithmeticAddCalculation' in content  # Check for child node name


# === Tests for classes used by ProcessDumpManager ===

@pytest.mark.usefixtures('aiida_profile_clean')
class TestProcessManagerHelpers:
    """Tests helper classes used by ProcessDumpManager."""

    def test_node_repo_io_dumper_mapping(self):
        """Test the IO mapping generation."""
        dumper_normal = NodeRepoIoDumper(DumpConfig(flat=False))
        mapping_normal = dumper_normal._generate_calculation_io_mapping(flat=False)
        assert mapping_normal.repository == 'inputs'
        assert mapping_normal.retrieved == 'outputs'
        assert mapping_normal.inputs == 'node_inputs'
        assert mapping_normal.outputs == 'node_outputs'

        dumper_flat = NodeRepoIoDumper(DumpConfig(flat=True))
        mapping_flat = dumper_flat._generate_calculation_io_mapping(flat=True)
        assert mapping_flat.repository == ''
        assert mapping_flat.retrieved == ''
        assert mapping_flat.inputs == ''
        assert mapping_flat.outputs == ''

    def test_workflow_walker(self, generate_workchain_multiply_add, tmp_path):
        """Test the WorkflowWalker traversal."""
        wc_node = generate_workchain_multiply_add()
        dump_target_path = tmp_path / f'walker_test_{wc_node.pk}'
        dump_target_path.mkdir()

        dumped_children = {}  # Store {uuid: path} of dumped children

        def mock_dump_processor(node: orm.ProcessNode, path: Path):
            """Mock function to record which children are processed."""
            dumped_children[node.uuid] = path

        walker = WorkflowWalker(dump_processor=mock_dump_processor)
        walker._dump_children(wc_node, dump_target_path)

        # Check that children were processed
        called_links = wc_node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all()
        child_uuids = {link.node.uuid for link in called_links}

        assert set(dumped_children.keys()) == child_uuids

        # Check paths look correct (e.g., contain the child label)
        multiply_node = called_links[0].node
        multiply_path = dumped_children[multiply_node.uuid]
        assert multiply_path.parent == dump_target_path
        assert multiply_path.name.startswith('01-multiply-')

        # Example for the second child (add)
        add_node = called_links[1].node
        add_path = dumped_children[add_node.uuid]
        assert add_path.parent == dump_target_path
        assert add_path.name.startswith('02-ArithmeticAddCalculation-')

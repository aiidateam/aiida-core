###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the dumping of process data to disk."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.process import ProcessDumper

# Non-AiiDA variables
filename = 'file.txt'
filecontent = 'a'
inputs_relpath = Path('inputs')
outputs_relpath = Path('outputs')
node_inputs_relpath = Path('node_inputs')
node_outputs_relpath = Path('node_outputs')
default_dump_paths = [inputs_relpath, outputs_relpath, node_inputs_relpath, node_outputs_relpath]
custom_dump_paths = [f'{path}_' for path in default_dump_paths]

# Define variables used for constructing the nodes used to test the dumping
singlefiledata_linklabel = 'singlefile'
folderdata_linklabel = 'folderdata'
folderdata_relpath = Path('relative_path')
folderdata_test_path = folderdata_linklabel / folderdata_relpath
arraydata_linklabel = 'arraydata'
node_metadata_file = '.aiida_node_metadata.yaml'


# Only test top-level actions, like path and README creation
# Other things tested via `_dump_workflow` and `_dump_calculation`
@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump(generate_calculation_node_io, generate_workchain_node_io, tmp_path):
    from aiida.tools.archive.exceptions import ExportValidationError

    dump_parent_path = tmp_path / 'wc-dump-test-io'
    process_dumper = ProcessDumper()
    # Don't attach outputs, as it would require storing the calculation_node and then it cannot be used in the workchain
    cj_nodes = [generate_calculation_node_io(attach_outputs=False), generate_calculation_node_io(attach_outputs=False)]
    wc_node = generate_workchain_node_io(cj_nodes=cj_nodes)

    # Raises if ProcessNode not sealed
    with pytest.raises(ExportValidationError):
        return_path = process_dumper.dump(process_node=wc_node, output_path=dump_parent_path)

    wc_node.seal()
    return_path = process_dumper.dump(process_node=wc_node, output_path=dump_parent_path)

    assert dump_parent_path.is_dir()
    assert (dump_parent_path / 'README.md').is_file()
    assert return_path == dump_parent_path


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_workflow(generate_calculation_node_io, generate_workchain_node_io, tmp_path):
    # Need to generate parent path for dumping, as I don't want the sub-workchains to be dumped directly into `tmp_path`
    dump_parent_path = tmp_path / 'wc-workflow_dump-test-io'
    process_dumper = ProcessDumper()
    # Don't attach outputs, as it would require storing the calculation_node and then it cannot be used in the workchain
    cj_nodes = [generate_calculation_node_io(attach_outputs=False), generate_calculation_node_io(attach_outputs=False)]
    wc_node = generate_workchain_node_io(cj_nodes=cj_nodes)
    process_dumper._dump_workflow(workflow_node=wc_node, output_path=dump_parent_path)

    base_path = Path('01-sub_workflow-8/01-calculation-9')
    input_path = base_path / 'inputs/file.txt'
    singlefiledata_path = base_path / 'node_inputs/singlefile/file.txt'
    folderdata_path = base_path / 'node_inputs/folderdata/relative_path/file.txt'
    arraydata_path = base_path / 'node_inputs/arraydata/default.npy'
    node_metadata_paths = [
        node_metadata_file,
        f'01-sub_workflow-8/{node_metadata_file}',
        f'{base_path}/{node_metadata_file}',
        f'01-sub_workflow-8/02-calculation-10/{node_metadata_file}',
    ]

    expected_files = [input_path, singlefiledata_path, folderdata_path, arraydata_path, *node_metadata_paths]
    expected_files = [dump_parent_path / expected_file for expected_file in expected_files]

    assert all([expected_file.is_file() for expected_file in expected_files])

    # Flat dumping
    dump_parent_path = tmp_path / 'wc-dump-test-io-flat'
    process_dumper = ProcessDumper(flat=True)
    process_dumper._dump_workflow(workflow_node=wc_node, output_path=dump_parent_path)

    input_path = base_path / 'file.txt'
    arraydata_path = base_path / 'default.npy'
    folderdata_path = base_path / 'relative_path/file.txt'
    node_metadata_paths = [
        node_metadata_file,
        f'01-sub_workflow-8/{node_metadata_file}',
        f'{base_path}/{node_metadata_file}',
        f'01-sub_workflow-8/02-calculation-10/{node_metadata_file}',
    ]

    expected_files = [input_path, folderdata_path, arraydata_path, *node_metadata_paths]
    expected_files = [dump_parent_path / expected_file for expected_file in expected_files]

    assert all([expected_file.is_file() for expected_file in expected_files])


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_multiply_add(tmp_path, generate_workchain_multiply_add):
    dump_parent_path = tmp_path / 'wc-dump-test-multiply-add'
    process_dumper = ProcessDumper()
    wc_node = generate_workchain_multiply_add()
    process_dumper.dump(process_node=wc_node, output_path=dump_parent_path)

    arithmetic_add_path = dump_parent_path / '02-ArithmeticAddCalculation-8'
    multiply_path = dump_parent_path / '01-multiply-6'

    input_files = [
        '_aiidasubmit.sh',
        'aiida.in',
        '.aiida/job_tmpl.json',
        '.aiida/calcinfo.json',
    ]
    output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']

    input_files = [arithmetic_add_path / inputs_relpath / input_file for input_file in input_files]
    input_files += [multiply_path / inputs_relpath / 'source_file']
    output_files = [arithmetic_add_path / outputs_relpath / output_file for output_file in output_files]

    # No node_inputs contained in MultiplyAddWorkChain
    assert all([input_file.is_file() for input_file in input_files])
    assert all([output_file.is_file() for output_file in output_files])

    # Flat dumping
    dump_parent_path = tmp_path / 'wc-dump-test-multiply-add-flat'
    process_dumper = ProcessDumper(flat=True)
    process_dumper.dump(process_node=wc_node, output_path=dump_parent_path)

    multiply_file = dump_parent_path / '01-multiply-6' / 'source_file'
    arithmetic_add_files = [
        '_aiidasubmit.sh',
        'aiida.in',
        '.aiida/job_tmpl.json',
        '.aiida/calcinfo.json',
        '_scheduler-stderr.txt',
        '_scheduler-stdout.txt',
        'aiida.out',
    ]
    arithmetic_add_files = [
        dump_parent_path / '02-ArithmeticAddCalculation-8' / arithmetic_add_file
        for arithmetic_add_file in arithmetic_add_files
    ]

    assert multiply_file.is_file()
    assert all([expected_file.is_file() for expected_file in arithmetic_add_files])


# Tests for dump_calculation method
def test_dump_calculation_node(tmp_path, generate_calculation_node_io):
    # Checking the actual content should be handled by `test_copy_tree`

    # Normal dumping -> node_inputs and not flat; no paths provided
    dump_parent_path = tmp_path / 'cj-dump-test-io'
    process_dumper = ProcessDumper(include_outputs=True)
    calculation_node = generate_calculation_node_io()
    process_dumper._dump_calculation(calculation_node=calculation_node, output_path=dump_parent_path)

    assert (dump_parent_path / inputs_relpath / filename).is_file()
    assert (dump_parent_path / node_inputs_relpath / singlefiledata_linklabel / filename).is_file()
    assert (dump_parent_path / node_inputs_relpath / folderdata_test_path / filename).is_file()
    assert (dump_parent_path / node_inputs_relpath / arraydata_linklabel / 'default.npy').is_file()

    assert (dump_parent_path / node_outputs_relpath / singlefiledata_linklabel / filename).is_file()
    assert (dump_parent_path / node_outputs_relpath / folderdata_test_path / filename).is_file()

    # Check contents once
    with open(dump_parent_path / inputs_relpath / filename, 'r') as handle:
        assert handle.read() == filecontent
    with open(dump_parent_path / node_inputs_relpath / singlefiledata_linklabel / filename) as handle:
        assert handle.read() == filecontent
    with open(dump_parent_path / node_inputs_relpath / folderdata_test_path / filename) as handle:
        assert handle.read() == filecontent
    with open(dump_parent_path / node_outputs_relpath / singlefiledata_linklabel / filename) as handle:
        assert handle.read() == filecontent
    with open(dump_parent_path / node_outputs_relpath / folderdata_test_path / filename) as handle:
        assert handle.read() == filecontent


def test_dump_calculation_flat(tmp_path, generate_calculation_node_io):
    # Flat dumping -> no paths provided -> Default paths should not be existent.
    # Internal FolderData structure retained.
    dump_parent_path = tmp_path / 'cj-dump-test-custom'
    process_dumper = ProcessDumper(flat=True)
    calculation_node = generate_calculation_node_io()
    process_dumper._dump_calculation(calculation_node=calculation_node, output_path=dump_parent_path)

    # Here, the same file will be written by inputs and node_outputs and node_inputs
    # So it should only be present once in the parent dump directory
    assert not (dump_parent_path / inputs_relpath).is_dir()
    assert not (dump_parent_path / node_inputs_relpath).is_dir()
    assert not (dump_parent_path / outputs_relpath).is_dir()
    assert (dump_parent_path / filename).is_file()
    assert (dump_parent_path / 'default.npy').is_file()
    assert (dump_parent_path / folderdata_relpath / filename).is_file()


# Here, in principle, test only non-default arguments, as defaults tested above
def test_dump_calculation_overwr_incr(tmp_path, generate_calculation_node_io):
    """Tests the ProcessDumper for the overwrite and incremental option."""
    dump_parent_path = tmp_path / 'cj-dump-test-overwrite'
    base_dumper = BaseDumper(overwrite=False, incremental=False)
    process_dumper = ProcessDumper(base_dumper=base_dumper)
    calculation_node = generate_calculation_node_io()
    calculation_node.seal()
    # Create safeguard file to mock existing dump directory
    dump_parent_path.mkdir()
    # we create safeguard file so the dumping works
    (dump_parent_path / '.aiida_node_metadata.yaml').touch()
    with pytest.raises(FileExistsError):
        process_dumper._dump_calculation(calculation_node=calculation_node, output_path=dump_parent_path)
    # With overwrite option true no error is raised and the dumping can run through.
    base_dumper = BaseDumper(overwrite=True, incremental=False)
    process_dumper = ProcessDumper(base_dumper=base_dumper)
    process_dumper._dump_calculation(calculation_node=calculation_node, output_path=dump_parent_path)
    assert (dump_parent_path / inputs_relpath / filename).is_file()

    shutil.rmtree(dump_parent_path)

    # Incremental also does work
    dump_parent_path.mkdir()
    (dump_parent_path / '.aiida_node_metadata.yaml').touch()
    base_dumper = BaseDumper(overwrite=False, incremental=True)
    process_dumper = ProcessDumper(base_dumper=base_dumper)
    process_dumper._dump_calculation(calculation_node=calculation_node, output_path=dump_parent_path)
    assert (dump_parent_path / inputs_relpath / filename).is_file()


# With both inputs and outputs being dumped is the standard test case above, so only test without inputs here
def test_dump_calculation_no_inputs(tmp_path, generate_calculation_node_io):
    dump_parent_path = tmp_path / 'cj-dump-test-noinputs'
    process_dumper = ProcessDumper(include_inputs=False)
    calculation_node = generate_calculation_node_io()
    process_dumper._dump_calculation(calculation_node=calculation_node, output_path=dump_parent_path)
    assert not (dump_parent_path / node_inputs_relpath).is_dir()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_calculation_add(tmp_path, generate_calculation_node_add):
    dump_parent_path = tmp_path / 'cj-dump-test-add'

    process_dumper = ProcessDumper()
    calculation_node_add = generate_calculation_node_add()
    process_dumper._dump_calculation(calculation_node=calculation_node_add, output_path=dump_parent_path)

    input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    input_files = [dump_parent_path / inputs_relpath / input_file for input_file in input_files]
    output_files = [dump_parent_path / outputs_relpath / output_file for output_file in output_files]

    assert all([input_file.is_file() for input_file in input_files])
    assert all([output_file.is_file() for output_file in output_files])


@pytest.mark.usefixtures('aiida_profile_clean')
def test_generate_default_dump_path(
    generate_calculation_node_add,
    generate_workchain_multiply_add,
):
    process_dumper = ProcessDumper()
    add_node = generate_calculation_node_add()
    multiply_add_node = generate_workchain_multiply_add()
    add_path = process_dumper._generate_default_dump_path(process_node=add_node)
    multiply_add_path = process_dumper._generate_default_dump_path(process_node=multiply_add_node)

    assert str(add_path) == f'dump-ArithmeticAddCalculation-{add_node.pk}'
    assert str(multiply_add_path) == f'dump-MultiplyAddWorkChain-{multiply_add_node.pk}'


def test_generate_calculation_io_mapping():
    process_dumper = ProcessDumper()
    calculation_io_mapping = process_dumper._generate_calculation_io_mapping()
    assert calculation_io_mapping.repository == 'inputs'
    assert calculation_io_mapping.retrieved == 'outputs'
    assert calculation_io_mapping.inputs == 'node_inputs'
    assert calculation_io_mapping.outputs == 'node_outputs'

    calculation_io_mapping = process_dumper._generate_calculation_io_mapping(io_dump_paths=custom_dump_paths)
    assert calculation_io_mapping.repository == 'inputs_'
    assert calculation_io_mapping.retrieved == 'outputs_'
    assert calculation_io_mapping.inputs == 'node_inputs_'
    assert calculation_io_mapping.outputs == 'node_outputs_'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_generate_child_node_label(
    generate_workchain_multiply_add, generate_calculation_node_io, generate_workchain_node_io
):
    # Check with manually constructed, more complex workchain
    cj_node = generate_calculation_node_io(attach_outputs=False)
    wc_node = generate_workchain_node_io(cj_nodes=[cj_node])
    wc_output_triples = wc_node.base.links.get_outgoing().all()
    sub_wc_node = wc_output_triples[0].node

    output_triples = wc_output_triples + sub_wc_node.base.links.get_outgoing().all()
    # Sort by mtime here, not ctime, as I'm actually creating the CalculationNode first.
    output_triples = sorted(output_triples, key=lambda link_triple: link_triple.node.mtime)

    process_dumper = ProcessDumper()

    output_paths = sorted(
        [
            process_dumper._generate_child_node_label(index, output_node)
            for index, output_node in enumerate(output_triples)
        ]
    )
    assert output_paths == ['00-sub_workflow-5', '01-calculation-6']

    # Check with multiply_add workchain node
    multiply_add_node = generate_workchain_multiply_add()
    output_triples = multiply_add_node.base.links.get_outgoing().all()
    # Sort by ctime here, not mtime, as I'm generating the WorkChain normally
    output_triples = sorted(output_triples, key=lambda link_triple: link_triple.node.ctime)
    output_paths = sorted(
        [process_dumper._generate_child_node_label(_, output_node) for _, output_node in enumerate(output_triples)]
    )
    print(output_paths)
    assert output_paths == ['00-multiply-12', '01-ArithmeticAddCalculation-14', '02-result-17']


def test_dump_node_yaml(generate_calculation_node_io, tmp_path, generate_workchain_multiply_add):
    process_dumper = ProcessDumper()
    cj_node = generate_calculation_node_io(attach_outputs=False)
    process_dumper._dump_node_yaml(process_node=cj_node, output_path=tmp_path)

    assert (tmp_path / node_metadata_file).is_file()

    # Test with multiply_add
    wc_node = generate_workchain_multiply_add()
    process_dumper._dump_node_yaml(process_node=wc_node, output_path=tmp_path)

    assert (tmp_path / node_metadata_file).is_file()

    # Open the dumped YAML file and read its contents
    with open(tmp_path / node_metadata_file, 'r') as dumped_file:
        contents = dumped_file.read()

    # Check if contents as expected
    assert 'Node data:' in contents
    assert 'User data:' in contents
    # Computer is None for the locally run MultiplyAdd
    assert 'Computer data:' not in contents
    assert 'Node attributes:' in contents
    assert 'Node extras:' in contents

    process_dumper = ProcessDumper(include_attributes=False, include_extras=False)

    (tmp_path / node_metadata_file).unlink()
    process_dumper._dump_node_yaml(process_node=wc_node, output_path=tmp_path)

    # Open the dumped YAML file and read its contents
    with open(tmp_path / node_metadata_file, 'r') as dumped_file:
        contents = dumped_file.read()

    # Check if contents as expected -> No attributes and extras
    assert 'Node data:' in contents
    assert 'User data:' in contents
    # Computer is None for the locally run MultiplyAdd
    assert 'Computer data:' not in contents
    assert 'Node attributes:' not in contents
    assert 'Node extras:' not in contents


def test_generate_parent_readme(tmp_path, generate_workchain_multiply_add):
    wc_node = generate_workchain_multiply_add()
    process_dumper = ProcessDumper()

    process_dumper._generate_readme(process_node=wc_node, output_path=tmp_path)

    assert (tmp_path / 'README.md').is_file()

    with open(tmp_path / 'README.md', 'r') as dumped_file:
        contents = dumped_file.read()

    assert 'This directory contains' in contents
    assert '`MultiplyAddWorkChain' in contents
    assert 'ArithmeticAddCalculation' in contents
    # Check for outputs of `verdi process status/report/show`
    assert 'Finished [0] [3:result]' in contents
    assert 'Property     Value' in contents
    assert 'There are 1 log messages for this calculation' in contents

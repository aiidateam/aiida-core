###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the dumping of ProcessNode data to disk."""

# ? For testing the dumping, one either needs to cd into the tmp_path, or pass the tmp_path as argument, otherwise, the
# ? files are dumped into src -> CWD from where the script is run.
# ? However, when one passes tmp_dir as output_path, no automatic path is created, as not at the default value is set,
# ? so str(output_path) == '.' is False

import pathlib
import shutil
from pathlib import Path

import pytest
from aiida.tools.dumping.processes import (
    calculation_node_dump,
    calculation_node_inputs_dump,
    generate_default_dump_path,
    generate_node_input_label,
    process_node_dump,
    validate_make_dump_path,
)

# Define parameters for the dumping
filename = 'file.txt'
filecontent = 'a'
raw_inputs_relpath = 'raw_inputs'
raw_outputs_relpath = 'raw_outputs'
node_inputs_relpath = 'node_inputs'
default_dump_paths = [raw_inputs_relpath, raw_outputs_relpath, node_inputs_relpath]
custom_dump_paths = [f'{path}_' for path in default_dump_paths]

# Define some variables used for constructing the nodes used to test the dumping
singlefiledata_linklabel = 'singlefile_input'
folderdata_linklabel = 'folderdata_input'
folderdata_internal_path = 'relative_path'
folderdata_path = pathlib.Path(f'{folderdata_linklabel}/{folderdata_internal_path}')


# ? Move this somewhere else?
def clean_tmp_path(tmp_path: Path):
    """
    Recursively delete files and directories in a path, e.g. a temporary path used by pytest.
    # ? This empties the directory, as intended for the general dumping directory, but doesn't delete it itself
    """

    for item in tmp_path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def test_calcjob_node_inputs_dump(tmp_path, generate_calcjob_node_io):
    """Test that dumping of CalcJob node inputs works correctly."""

    calcjob_node = generate_calcjob_node_io()
    dump_parent_path = tmp_path / node_inputs_relpath

    # Check the dumping results with flat=False

    # Expected tree:
    # node_inputs
    # ├── folderdata_input
    # │  └── relative_path
    # │     └── file.txt
    # └── singlefile_input
    #    └── file.txt

    calculation_node_inputs_dump(calculation_node=calcjob_node, output_path=dump_parent_path)
    assert (dump_parent_path / singlefiledata_linklabel).is_dir()
    assert (dump_parent_path / singlefiledata_linklabel / filename).is_file()
    assert (dump_parent_path / folderdata_path).is_dir()
    assert (dump_parent_path / folderdata_path / filename).is_file()

    with open(dump_parent_path / singlefiledata_linklabel / filename, 'r') as handle:
        assert handle.read() == filecontent

    with open(dump_parent_path / folderdata_path / filename, 'r') as handle:
        assert handle.read() == filecontent

    # Probably not actually necessary, as in the previous step they are dumped to `node_inputs`
    clean_tmp_path(tmp_path=tmp_path)

    # Check the dumping results with flat=True

    # Expected tree:
    # node_inputs
    # ├── file.txt
    # └── relative_path
    #     └── file.txt

    calculation_node_inputs_dump(calculation_node=calcjob_node, output_path=dump_parent_path, flat=True)

    # Flat=True doesn't flatten nested directory structure of FolderData objects -> Leave relative path
    assert (dump_parent_path / folderdata_internal_path).is_dir()
    assert (dump_parent_path / folderdata_internal_path / filename).is_file()

    assert (dump_parent_path / filename).is_file()
    with open(dump_parent_path / filename, 'r') as handle:
        assert handle.read() == filecontent

    with open(dump_parent_path / folderdata_internal_path / filename, 'r') as handle:
        assert handle.read() == filecontent

    # todo: test here with ArithmeticAdd as well


def test_calcjob_dump_io(generate_calcjob_node_io, tmp_path):

    dump_parent_path = tmp_path / 'cj-dump-test-io'

    # Here, check for attached `retrieved` outputs, as well
    calcjob_node = generate_calcjob_node_io()

    # todo: Test for _LOGGER.info outputs
    # Checking the actual content should be handled by `test_copy_tree`
    # Not testing for the folderdata-input here, as this should be covered by `test_calcjob_node_inputs_dump`
    # It is dumped to 'relative_path/file.txt' in all cases, though, but just ignore

    # Normal dumping -> node_inputs and not flat; no paths provided

    # Expected tree:
    # cj-dump-test-io
    # ├── node_inputs
    # │  ├── folderdata_input
    # │  │  └── relative_path
    # │  │     └── file.txt
    # │  └── singlefile_input
    # │     └── file.txt
    # ├── raw_inputs
    # │  └── file.txt
    # └── raw_outputs
    #    └── file.txt

    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path)

    assert (dump_parent_path / default_dump_paths[0] / filename).is_file()
    assert (dump_parent_path / default_dump_paths[1] / filename).is_file()
    assert (dump_parent_path / default_dump_paths[2] / singlefiledata_linklabel / filename).is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Normal dumping -> node_inputs and not flat; custom paths provided

    # Expected tree:
    # cj-dump-test-io
    # ├── node_inputs_
    # │  ├── folderdata_input
    # │  │  └── relative_path
    # │  │     └── file.txt
    # │  └── singlefile_input
    # │     └── file.txt
    # ├── raw_inputs_
    # │  └── file.txt
    # └── raw_outputs_
    #    └── file.txt

    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, io_dump_paths=custom_dump_paths)
    assert (dump_parent_path / custom_dump_paths[0] / filename).is_file()  # raw_inputs
    assert (dump_parent_path / custom_dump_paths[1] / filename).is_file()  # raw_outputs
    # node_inputs, singlefile
    assert (dump_parent_path / custom_dump_paths[2] / singlefiledata_linklabel / filename).is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Flat dumping -> no paths provided -> Default paths should not be existent. Internal FolderData structure retained.
    # Expected tree:
    # cj-dump-test-io
    # ├── file.txt
    # └── relative_path
    #     └── file.txt

    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, flat=True)
    assert not (dump_parent_path / default_dump_paths[0] / filename).is_file()  # raw_inputs
    assert not (dump_parent_path / default_dump_paths[1] / filename).is_file()  # raw_outputs
    assert not (dump_parent_path / default_dump_paths[2] / filename).is_file()  # node_inputs, singlefile
    # Here, the same file will be written by raw_inputs and raw_outputs and node_inputs
    # So it should only be present in the parent dump directory
    assert (dump_parent_path / filename).is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Flat dumping -> node_inputs and custom paths provided -> Test in custom paths,
    # But no subdirectories named after the link-labels under `node_inputs_`
    # Expected path:
    # cj-dump-test-io
    # ├── node_inputs_
    # │  ├── file.txt
    # │  └── relative_path
    # │     └── file.txt
    # ├── raw_inputs_
    # │  └── file.txt
    # └── raw_outputs_
    #    └── file.txt

    # todo: Test case of splitting the nested node_inputs based on double-underscore splitting not covered with the test
    # todo: setup. This might be again too specific for QE?
    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, io_dump_paths=custom_dump_paths, flat=True)
    assert (dump_parent_path / custom_dump_paths[0] / filename).is_file()  # raw_inputs
    assert (dump_parent_path / custom_dump_paths[1] / filename).is_file()  # raw_outputs
    assert (dump_parent_path / custom_dump_paths[2] / filename).is_file()  # node_inputs, singlefile

    clean_tmp_path(tmp_path=tmp_path)

    # Don't dump the connected node inputs for both, flat is True/False
    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, include_inputs=False)
    assert not (dump_parent_path / custom_dump_paths[2]).is_dir()

    clean_tmp_path(tmp_path=tmp_path)

    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, include_inputs=False, flat=True)
    assert not (dump_parent_path / custom_dump_paths[2]).is_dir()

    clean_tmp_path(tmp_path=tmp_path)

    # Check that it fails when it tries to create the same directory without overwrite=True
    calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, overwrite=False)
    with pytest.raises(FileExistsError):
        calculation_node_dump(calcjob_node=calcjob_node, output_path=dump_parent_path, overwrite=False)


def test_calcjob_dump_arithmetic_add(tmp_path, aiida_localhost, generate_arithmetic_add_node):
    dump_path = tmp_path / 'calcjob_dump_arithmetic_add'

    # Now, generate `CalcJobNode` from ArithmeticAddCalculation
    add_node = generate_arithmetic_add_node(computer=aiida_localhost)

    # Normal dumping of ArithmeticAddCalculation node
    calculation_node_dump(calcjob_node=add_node, output_path=dump_path)

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [dump_path / default_dump_paths[0] / raw_input_file for raw_input_file in raw_input_files]
    raw_output_files = [dump_path / default_dump_paths[1] / raw_output_file for raw_output_file in raw_output_files]

    assert all([raw_input_file.is_file() for raw_input_file in raw_input_files])
    assert all([raw_output_file.is_file() for raw_output_file in raw_output_files])

    clean_tmp_path(tmp_path=tmp_path)


def test_process_dump_io(generate_calcjob_node_io, generate_workchain_node_io, tmp_path):

    # Expected tree:
    # wc-dump-test-io
    # └── 01-sub_workchain
    #     └── 01-calcjob
    #         ├── node_inputs
    #         │  ├── folderdata_input
    #         │  │  └── relative_path
    #         │  │     └── file.txt
    #         │  └── singlefile_input
    #         │     └── file.txt
    #         └── raw_inputs
    #             └── file.txt

    # Don't attach outputs, as this would require storing the calcjob_node, and it cannot be added. Dumping of outputs
    # should be taken care of by `test_calcjob_dump`
    cj_node = generate_calcjob_node_io(attach_outputs=False)
    wc_node = generate_workchain_node_io(cj_nodes=[cj_node])

    # Need to generate parent path for dumping, as I don't want the sub-workchains to be dumped directly into `tmp_path`
    # Other option would be to cd into `tmp_path` and then letting the default label be created
    dump_parent_path = tmp_path / 'wc-dump-test-io'

    # Don't test for `README` here, as this is only created when dumping is done via `verdi`
    raw_input_path = '01-sub_workchain/01-calcjob_0/raw_inputs/file.txt'
    singlefiledata_path = '01-sub_workchain/01-calcjob_0/node_inputs/singlefile_input/file.txt'
    folderdata_path = '01-sub_workchain/01-calcjob_0/node_inputs/folderdata_input/relative_path/file.txt'
    node_metadata_paths = [
        '.aiida_node_metadata.yaml',
        '01-sub_workchain/.aiida_node_metadata.yaml',
        '01-sub_workchain/01-calcjob_0/.aiida_node_metadata.yaml',
    ]

    expected_files = [raw_input_path, singlefiledata_path, folderdata_path, *node_metadata_paths]
    expected_files = [dump_parent_path / expected_file for expected_file in expected_files]

    process_node_dump(process_node=wc_node, output_path=dump_parent_path)

    assert all([expected_file.is_file() for expected_file in expected_files])

    clean_tmp_path(tmp_path=dump_parent_path)

    # Check directory tree when flat=True

    # Expected tree:
    # wc-dump-test-io
    # ├── file.txt
    # └── relative_path
    #     └── file.txt

    process_node_dump(process_node=wc_node, output_path=dump_parent_path, flat=True)
    assert (dump_parent_path / filename).is_file()
    # Internal hierarchy of the FolderData is retained
    assert (dump_parent_path / folderdata_internal_path / filename).is_file()

    clean_tmp_path(tmp_path=dump_parent_path)

    # Check that dumping fails if multiple CalcJobs run by the workchain if flat=True
    cj_nodes = [generate_calcjob_node_io(attach_outputs=False), generate_calcjob_node_io(attach_outputs=False)]
    wc_node = generate_workchain_node_io(cj_nodes=cj_nodes)
    with pytest.raises(NotImplementedError):
        process_node_dump(process_node=wc_node, output_path=dump_parent_path, flat=True)


def test_process_dump_multiply_add(tmp_path, generate_multiply_add_node, aiida_localhost):

    # Testing for files in hidden .aiida folder here, but not in more complex io functions
    dump_parent_path = tmp_path / 'multiply_add-dump-test'

    multiply_add_node = generate_multiply_add_node(computer=aiida_localhost)

    # Dump with flat=True
    # Expected tree:
    # multiply_add-dump-test
    # ├── .aiida
    # │  ├── calcinfo.json
    # │  └── job_tmpl.json
    # ├── .aiida_node_metadata.yaml
    # ├── _aiidasubmit.sh
    # ├── _scheduler-stderr.txt
    # ├── _scheduler-stdout.txt
    # ├── aiida.in
    # ├── aiida.out
    #!└── source_file missing

    process_node_dump(process_node=multiply_add_node, output_path=dump_parent_path, flat=True)

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_input_files += ['source_file']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [dump_parent_path / raw_input_file for raw_input_file in raw_input_files]
    raw_output_files = [dump_parent_path / raw_output_file for raw_output_file in raw_output_files]

    print(multiply_add_node.called_descendants)
    print(multiply_add_node.called_descendants[0])
    print(type(multiply_add_node.called_descendants[0]))
    print(multiply_add_node.called_descendants[0].base.repository.list_objects())
    print(multiply_add_node.called_descendants[0].base.repository.list_object_names())

    # ! source_file is missing -> Why?
    assert all([raw_input_file.is_file() for raw_input_file in raw_input_files])
    assert all([raw_output_file.is_file() for raw_output_file in raw_output_files])

    clean_tmp_path(tmp_path=tmp_path)

    # Dump with flat=False
    # Expected tree:
    # multiply_add-dump-test
    # ├── 01-multiply
    # │  └── raw_inputs
    # │     └── source_file
    # └── 02-ArithmeticAddCalculation
    #    ├── raw_inputs
    #    │  ├── .aiida
    #    │  │  ├── calcinfo.json
    #    │  │  └── job_tmpl.json
    #    │  ├── _aiidasubmit.sh
    #    │  └── aiida.in
    #    └── raw_outputs
    #       ├── _scheduler-stderr.txt
    #       ├── _scheduler-stdout.txt
    #       └── aiida.out

    process_node_dump(process_node=multiply_add_node, output_path=dump_parent_path)

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [
        dump_parent_path / '02-ArithmeticAddCalculation' / default_dump_paths[0] / raw_input_file
        for raw_input_file in raw_input_files
    ]
    raw_input_files += [dump_parent_path / '01-multiply' / default_dump_paths[0] / 'source_file']
    raw_output_files = [
        dump_parent_path / '02-ArithmeticAddCalculation' / default_dump_paths[1] / raw_output_file
        for raw_output_file in raw_output_files
    ]
    # No node_inputs contained in MultiplyAddWorkChain

    assert all([raw_input_file.is_file() for raw_input_file in raw_input_files])
    assert all([raw_output_file.is_file() for raw_output_file in raw_output_files])




def test_generate_default_dump_path(generate_arithmetic_add_node, generate_multiply_add_node, aiida_localhost):

    add_node = generate_arithmetic_add_node(computer=aiida_localhost)
    multiply_add_node = generate_multiply_add_node(computer=aiida_localhost)
    add_path = generate_default_dump_path(process_node=add_node)
    multiply_add_path = generate_default_dump_path(process_node=multiply_add_node)

    # ? Possible to reset db here to make pks reproducible?
    assert str(add_path) == f'dump-ArithmeticAddCalculation-{add_node.pk}'
    assert str(multiply_add_path) == f'dump-MultiplyAddWorkChain-{multiply_add_node.pk}'

    # todo: test for io_function?


def test_generate_node_input_label(
    generate_multiply_add_node, generate_calcjob_node_io, generate_workchain_node_io, aiida_localhost
):
    # Check with manually constructed, more complex workchain
    cj_node = generate_calcjob_node_io(attach_outputs=False)
    wc_node = generate_workchain_node_io(cj_nodes=[cj_node])
    wc_output_triples = wc_node.base.links.get_outgoing().all()
    sub_wc_node = wc_output_triples[0].node

    output_triples = wc_output_triples + sub_wc_node.base.links.get_outgoing().all()

    output_labels = sorted([generate_node_input_label(_, output_node) for _, output_node in enumerate(output_triples)])
    assert output_labels == ['00-sub_workchain', '01-calcjob_0']

    # Check with multiply_add workchain node
    multiply_add_node = generate_multiply_add_node(computer=aiida_localhost)
    output_triples = multiply_add_node.base.links.get_outgoing().all()
    output_labels = sorted([generate_node_input_label(_, output_node) for _, output_node in enumerate(output_triples)])
    assert output_labels == ['00-multiply', '01-ArithmeticAddCalculation', '02-result']


def test_validate_make_dump_path(chdir_tmp_path, tmp_path):

    chdir_tmp_path

    test_dir = Path('test-dir')
    test_dir_abs = tmp_path / test_dir
    safeguard_file = '.aiida_node_metadata.yaml'

    # Path must be provided
    with pytest.raises(TypeError):
        validate_make_dump_path()

    # Check if path created if non-existent
    output_path = validate_make_dump_path(path=test_dir)
    assert output_path == test_dir_abs

    clean_tmp_path(tmp_path=tmp_path)

    # Empty path is fine -> No error and full path returned
    test_dir_abs.mkdir()
    output_path = validate_make_dump_path(path=test_dir)
    assert output_path == test_dir_abs

    clean_tmp_path(tmp_path=tmp_path)

    # Fails if directory not empty and overwrite set to False
    test_dir_abs.mkdir()
    (test_dir_abs / filename).touch()
    with pytest.raises(FileExistsError):
        output_path = validate_make_dump_path(path=test_dir)
    assert (test_dir_abs / filename).is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Fails if directory not empty and overwrite set to True, but safeguard_file not found (for safety reasons)
    test_dir_abs.mkdir()
    (test_dir_abs / filename).touch()
    with pytest.raises(FileExistsError):
        output_path = validate_make_dump_path(path=test_dir, overwrite=True)
    assert (test_dir_abs / filename).is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Works if directory not empty, but overwrite=True and safeguard_file (e.g. `.aiida_node_metadata.yaml`) contained
    test_dir_abs.mkdir()
    (test_dir_abs / safeguard_file).touch()
    output_path = validate_make_dump_path(path=test_dir, overwrite=True, safeguard_file=safeguard_file)
    assert output_path == test_dir_abs
    assert not (test_dir_abs / safeguard_file).is_file()


def test_dump_yaml():
    assert False

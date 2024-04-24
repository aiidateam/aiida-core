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
    calcjob_dump,
    calcjob_node_inputs_dump,
    generate_default_dump_path,
    generate_node_input_label,
    process_dump,
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
folderdata_relative_path = 'relative_path'
folderdata_path = pathlib.Path(f'{folderdata_linklabel}/{folderdata_relative_path}')


# ? Move this somewhere else
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
    tmp_path_nested = tmp_path / node_inputs_relpath

    # Test the dumping results with flat=False
    calcjob_node_inputs_dump(calcjob_node=calcjob_node, output_path=tmp_path_nested, flat=False)

    singlefiledata_outputpath = tmp_path_nested / singlefiledata_linklabel
    singlefiledata_outputfile = singlefiledata_outputpath / filename
    folderdata_outputpath = tmp_path_nested / folderdata_path
    folderdata_outputfile = folderdata_outputpath / filename

    assert singlefiledata_outputpath.is_dir()
    assert singlefiledata_outputfile.is_file()
    with open(singlefiledata_outputfile, 'r') as handle:
        assert handle.read() == filecontent

    assert folderdata_outputpath.is_dir()
    assert folderdata_outputfile.is_file()
    with open(folderdata_outputfile, 'r') as handle:
        assert handle.read() == filecontent

    # Probably not actually necessary, as in the previous step they are dumped to `node_inputs`
    clean_tmp_path(tmp_path=tmp_path)

    # Test the dumping results with flat=True
    calcjob_node_inputs_dump(calcjob_node=calcjob_node, output_path=tmp_path, flat=True)

    singlefiledata_outputfile = tmp_path / filename

    # Flat=True doesn't flatten nested directory structure of FolderData objects -> Leave relative path
    folderdata_outputpath = tmp_path / folderdata_relative_path
    folderdata_outputfile = folderdata_outputpath / filename

    assert singlefiledata_outputfile.is_file()
    with open(singlefiledata_outputfile, 'r') as handle:
        assert handle.read() == filecontent

    assert folderdata_outputpath.is_dir()
    assert folderdata_outputfile.is_file()
    with open(folderdata_outputfile, 'r') as handle:
        assert handle.read() == filecontent


def test_calcjob_dump_io(generate_calcjob_node_io, tmp_path):
    dump_path = tmp_path / 'calcjob_dump_io'

    calcjob_node = generate_calcjob_node_io()

    # todo: Test for _LOGGER.info outputs
    # todo: Replace repititions for raw_input/output and node_inputs with loops
    # Checking the actual content should be handled by `test_copy_tree`
    # Not testing for the folderdata-input here, as this should be covered by `test_calcjob_node_inputs_dump`
    # It is dumped to 'relative_path/file.txt' in all cases, though, but just ignore

    # Normal dumping -> node_inputs and not flat; no paths provided
    calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path)

    raw_input_file = dump_path / default_dump_paths[0] / filename
    raw_output_file = dump_path / default_dump_paths[1] / filename
    node_inputs_file = dump_path / default_dump_paths[2] / singlefiledata_linklabel / filename
    assert raw_input_file.is_file()
    assert raw_output_file.is_file()
    assert node_inputs_file.is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Normal dumping -> node_inputs and not flat; custom paths provided
    calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, io_dump_paths=custom_dump_paths)
    assert (dump_path / custom_dump_paths[0] / filename).is_file()  # raw_inputs
    assert (dump_path / custom_dump_paths[1] / filename).is_file()  # raw_outputs
    assert (dump_path / custom_dump_paths[2] / singlefiledata_linklabel / filename).is_file()  # node_inputs, singlefile

    # Flat dumping -> no node_inputs and no paths provided -> Default paths should not be existent
    calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, flat=True)
    assert not (dump_path / default_dump_paths[0] / filename).is_file()  # raw_inputs
    assert not (dump_path / default_dump_paths[1] / filename).is_file()  # raw_outputs
    assert not (dump_path / default_dump_paths[2] / filename).is_file()  # node_inputs, singlefile
    # Here, the same file will be written by raw_inputs and raw_outputs and node_inputs
    # So it should only be present in the parent dump directory
    assert (dump_path / filename).is_file()

    clean_tmp_path(tmp_path=tmp_path)

    # Flat dumping -> node_inputs and custom paths provided -> Test in custom paths
    # todo: Test case of splitting the nested node_inputs based on double-underscore splitting not covered with the test
    # todo: setup. This might be again too specific for QE? Like this, it's basically the same as the non-flat custom
    # todo: path test above
    calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, io_dump_paths=custom_dump_paths, flat=True)
    assert (dump_path / custom_dump_paths[0] / filename).is_file()  # raw_inputs
    assert (dump_path / custom_dump_paths[1] / filename).is_file()  # raw_outputs
    assert (dump_path / custom_dump_paths[2] / filename).is_file()  # node_inputs, singlefile
    # Could be shorter in that case, but not all of them, and listed might be more clear
    # assert all((dump_path / path / filename).is_file() for path in custom_dump_paths)

    clean_tmp_path(tmp_path=tmp_path)

    # Don't dump the connected node inputs
    calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, include_inputs=False)
    assert not (dump_path / custom_dump_paths[2] / singlefiledata_linklabel / filename).is_file()

    # Test that it fails when it tries to overwrite without overwrite=True
    with pytest.raises(FileExistsError):
        calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, overwrite=False)


def test_calcjob_dump_arithmetic_add(tmp_path, aiida_localhost, generate_arithmetic_add_node):
    dump_path = tmp_path / 'calcjob_dump_arithmetic_add'

    # Now, generate `CalcJobNode` from ArithmeticAddCalculation
    add_node = generate_arithmetic_add_node(computer=aiida_localhost)

    # Normal dumping of ArithmeticAddCalculation node
    calcjob_dump(calcjob_node=add_node, output_path=dump_path)

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [dump_path / default_dump_paths[0] / raw_input_file for raw_input_file in raw_input_files]
    raw_output_files = [dump_path / default_dump_paths[1] / raw_output_file for raw_output_file in raw_output_files]

    assert all([raw_input_file.is_file() for raw_input_file in raw_input_files])
    assert all([raw_output_file.is_file() for raw_output_file in raw_output_files])

    clean_tmp_path(tmp_path=tmp_path)


def test_process_dump_io(generate_work_chain_io, tmp_path):
    wc_node = generate_work_chain_io()

    dump_parent_path = tmp_path / 'wc-dump-test'

    raw_input_path = '01-sub_workchain/01-calcjob/raw_inputs/file.txt'
    singlefiledata_path = '01-sub_workchain/01-calcjob/node_inputs/singlefile_input/file.txt'
    folderdata_path = '01-sub_workchain/01-calcjob/node_inputs/folderdata_input/relative_path/file.txt'
    node_metadata_paths = [
        '.aiida_node_metadata.yaml',
        '01-sub_workchain/.aiida_node_metadata.yaml',
        '01-sub_workchain/01-calcjob/.aiida_node_metadata.yaml',
    ]
    # Don't test for `README` here, as this is only created when dumping is done via `verdi`
    expected_files = [raw_input_path, singlefiledata_path, folderdata_path, *node_metadata_paths]
    expected_files = [dump_parent_path / expected_file for expected_file in expected_files]

    # Here, when setting `output_path=tmp_path`, no parent directory for the parent workchain is created
    # Therefore, go into tmp-directory used for testing, without specifying output path -> Closer to how people might
    # actually use the function
    process_dump(process_node=wc_node, output_path=dump_parent_path)

    assert all([expected_file.is_file() for expected_file in expected_files])


def test_process_dump_multiply_add(tmp_path, generate_multiply_add_node, aiida_localhost):
    # Still set directory fixed to make dump directory reproducible (it should be anyway, but contains e.g. the pk)
    dump_parent_path = tmp_path / 'multiply_add-dump-test'

    # Now test for output from running MultiplyAddWorkChain
    multiply_add_node = generate_multiply_add_node(computer=aiida_localhost)

    process_dump(process_node=multiply_add_node, output_path=dump_parent_path)

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [
        dump_parent_path / '01-ArithmeticAddCalculation' / default_dump_paths[0] / raw_input_file
        for raw_input_file in raw_input_files
    ]
    raw_output_files = [
        dump_parent_path / '01-ArithmeticAddCalculation' / default_dump_paths[1] / raw_output_file
        for raw_output_file in raw_output_files
    ]

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


def test_generate_node_input_label(generate_multiply_add_node, generate_work_chain_io, aiida_localhost):
    # Test with MultiplyAddWorkChain inputs and outputs

    # Test with manually constructed, more complex workchain
    wc_node = generate_work_chain_io()
    wc_output_triples = wc_node.base.links.get_outgoing().all()
    sub_wc_node = wc_output_triples[0].node

    output_triples = wc_output_triples + sub_wc_node.base.links.get_outgoing().all()

    output_labels = [generate_node_input_label(_, output_node) for _, output_node in enumerate(output_triples)]
    assert output_labels == ['00-sub_workchain', '01-calcjob']

    # ? Not really testing for more complex cases that actually contain 'CALL' or 'iteration_' here


def test_validate_make_dump_path(chdir_tmp_path):
    pass


def test_dump_yaml():
    pass

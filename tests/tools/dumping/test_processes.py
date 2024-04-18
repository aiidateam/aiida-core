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

from aiida.tools.dumping.processes import (
    calcjob_dump,
    calcjob_node_inputs_dump,
    generate_default_dump_path,
    generate_node_input_label,
    workchain_dump,
)

filename = 'file.txt'

# Define some variables used for the dumping
node_inputs_relpath = 'node_inputs'
singlefiledata_linklabel = 'singlefile_input'
folderdata_linklabel = 'folderdata_input'
singlefiledata_path = pathlib.Path(f'{node_inputs_relpath}/{singlefiledata_linklabel}')
folderdata_path = pathlib.Path(f'{node_inputs_relpath}/{folderdata_linklabel}/relative_path')


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

    # Run the dumping
    calcjob_node_inputs_dump(calcjob_node=calcjob_node, output_path=tmp_path, inputs_relpath=node_inputs_relpath)

    # Test the dumping results
    singlefiledata_outputpath = pathlib.Path(tmp_path / singlefiledata_path)
    singlefiledata_outputfile = singlefiledata_outputpath / filename

    folderdata_outputpath = pathlib.Path(tmp_path / folderdata_path)
    folderdata_outputfile = folderdata_outputpath / filename

    assert singlefiledata_outputpath.is_dir()
    assert singlefiledata_outputfile.is_file()
    with open(singlefiledata_outputfile, 'r') as handle:
        assert handle.read() == 'a'

    assert folderdata_outputpath.is_dir()
    assert folderdata_outputfile.is_file()
    with open(folderdata_outputfile, 'r') as handle:
        assert handle.read() == 'a'


def test_calcjob_dump_io(generate_calcjob_node_io, tmp_path):
    dump_path = tmp_path / 'calcjob_dump_io'

    singlefiledata_outputpath = pathlib.Path(dump_path / singlefiledata_path)
    singlefiledata_outputfile = singlefiledata_outputpath / filename

    calcjob_node = generate_calcjob_node_io()
    raw_input_file = dump_path / 'raw_inputs' / filename
    raw_output_file = dump_path / 'raw_outputs' / filename

    # Normal dumping
    result = calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path)
    assert singlefiledata_outputfile.is_file()

    # Checking the actual content should be handled by `test_copy_tree`
    assert raw_input_file.is_file()
    assert raw_output_file.is_file()
    assert result

    clean_tmp_path(tmp_path=tmp_path)

    # Don't dump the connected node inputs
    result = calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, include_inputs=True)
    assert not singlefiledata_outputfile.is_file()
    assert result

    clean_tmp_path(tmp_path=tmp_path)

    # use_presubmit -> Depends on implementation from aiida-plugin, so I cannot test specifically inside aiida-core
    # Assert that `False` is returned if `use_presubmit` used, but no `process_type` has been set. This is the test case
    # one gets from the fixture (f'no process type for Node<{self.pk}>: cannot recreate process class')
    result = calcjob_dump(calcjob_node=calcjob_node, output_path=dump_path, use_presubmit=True)
    assert result is False

    clean_tmp_path(tmp_path=tmp_path)


def test_calcjob_dump_arithmetic_add(tmp_path, aiida_localhost, generate_arithmetic_add_node):
    dump_path = tmp_path / 'calcjob_dump_arithmetic_add'

    # Now, generate `CalcJobNode` from ArithmeticAddCalculation
    add_node = generate_arithmetic_add_node(computer=aiida_localhost)

    # Normal dumping of ArithmeticAddCalculation node
    result = calcjob_dump(calcjob_node=add_node, output_path=dump_path)
    assert result

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [dump_path / 'raw_inputs' / raw_input_file for raw_input_file in raw_input_files]
    raw_output_files = [dump_path / 'raw_outputs' / raw_output_file for raw_output_file in raw_output_files]

    assert all([raw_input_file.is_file() for raw_input_file in raw_input_files])
    assert all([raw_output_file.is_file() for raw_output_file in raw_output_files])

    clean_tmp_path(tmp_path=tmp_path)

    # Dumping with `use_presubmit` -> Directory structure is different and output file not dumped
    result = calcjob_dump(calcjob_node=add_node, output_path=dump_path, use_presubmit=True)

    assert result
    assert Path(dump_path / '_aiidasubmit.sh').is_file()
    assert Path(dump_path / 'aiida.in').is_file()
    assert not Path(dump_path / 'aiida.out').is_file()


def test_workchain_dump_io(generate_work_chain_io, tmp_path):
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
    result = workchain_dump(process_node=wc_node, output_path=dump_parent_path)

    assert result
    assert all([expected_file.is_file() for expected_file in expected_files])


def test_workchain_dump_multiply_add(tmp_path, generate_multiply_add_node, aiida_localhost):
    # Still set directory fixed to make dump directory reproducible (it should be anyway, but contains e.g. the pk)
    dump_parent_path = tmp_path / 'multiply_add-dump-test'

    # Now test for output from running MultiplyAddWorkChain
    multiply_add_node = generate_multiply_add_node(computer=aiida_localhost)

    result = workchain_dump(process_node=multiply_add_node, output_path=dump_parent_path)
    assert result

    raw_input_files = ['_aiidasubmit.sh', 'aiida.in', '.aiida/job_tmpl.json', '.aiida/calcinfo.json']
    raw_output_files = ['_scheduler-stderr.txt', '_scheduler-stdout.txt', 'aiida.out']
    raw_input_files = [
        dump_parent_path / '01-ArithmeticAddCalculation' / 'raw_inputs' / raw_input_file
        for raw_input_file in raw_input_files
    ]
    raw_output_files = [
        dump_parent_path / '01-ArithmeticAddCalculation' / 'raw_outputs' / raw_output_file
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

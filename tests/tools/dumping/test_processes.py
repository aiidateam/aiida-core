###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the dumping of ProcessNode data to disk."""

import io
import pathlib

from aiida.common import LinkType
from aiida.orm import FolderData, SinglefileData
from aiida.tools.dumping.processes import calcjob_node_inputs_dump


def test_calcjob_node_inputs_dump(generate_calculation_node, tmp_path):
    """Test that dumping of CalcJob node inputs works correctly."""

    # Set up labels and expected paths
    filename = 'file.txt'
    parent_name = 'node_inputs'
    singlefiledata_linklabel = 'singlefile_input'
    folderdata_linklabel = 'folderdata_input'
    singlefiledata_path = pathlib.Path(f'{parent_name}/{singlefiledata_linklabel}')
    folderdata_path = pathlib.Path(f'{parent_name}/{folderdata_linklabel}/relative_path')

    # Generate SinglefileData, Folderdata, and CalcJobNode nodes
    singlefiledata_node = SinglefileData.from_string(content='a', filename=filename)
    folderdata_node = FolderData()
    folderdata_node.put_object_from_filelike(io.StringIO('b'), path=pathlib.Path('relative_path') / filename)
    calcjob_node = generate_calculation_node()

    # Attach inputs to the CalcJobNode
    calcjob_node.base.links.add_incoming(
        singlefiledata_node,
        link_type=LinkType.INPUT_CALC,
        link_label=singlefiledata_linklabel,
    )
    calcjob_node.base.links.add_incoming(
        folderdata_node, link_type=LinkType.INPUT_CALC, link_label=folderdata_linklabel
    )

    # Run the dumping
    calcjob_node_inputs_dump(calcjob_node=calcjob_node, output_path=tmp_path, parent_name=parent_name)

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
        assert handle.read() == 'b'

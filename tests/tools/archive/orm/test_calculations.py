###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.CalcNode tests for the export and import routines"""

import pytest

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.links import LinkType
from aiida.engine import calcfunction
from aiida.tools.archive import create_archive, import_archive


@pytest.mark.requires_rmq
def test_calcfunction(tmp_path, aiida_profile):
    """Test @calcfunction"""
    aiida_profile.reset_storage()

    @calcfunction
    def add(a, b):
        """Add 2 numbers"""
        return {'res': orm.Float(a + b)}

    def max_(**kwargs):
        """Select the max value"""
        max_val = max((v.value, v) for v in kwargs.values())
        return {'res': max_val[1]}

    # I'm creating a bunch of numbers
    a, b, c, d, e = (orm.Float(i).store() for i in range(5))
    # this adds the maximum number between bcde to a.
    res = add(a=a, b=max_(b=b, c=c, d=d, e=e)['res'])['res']
    # These are the uuids that would be exported as well (as parents) if I wanted the final result
    uuids_values = [(a.uuid, a.value), (e.uuid, e.value), (res.uuid, res.value)]
    # These are the uuids that shouldn't be exported since it's a selection.
    not_wanted_uuids = [v.uuid for v in (b, c, d)]
    # At this point we export the generated data
    filename1 = tmp_path / 'export1.aiida'
    create_archive([res], filename=filename1, return_backward=True)
    aiida_profile.reset_storage()
    import_archive(filename1)
    # Check that the imported nodes are correctly imported and that the value is preserved
    for uuid, value in uuids_values:
        assert orm.load_node(uuid).value == value
    for uuid in not_wanted_uuids:
        with pytest.raises(NotExistent):
            orm.load_node(uuid)


def test_workcalculation(tmp_path, aiida_profile):
    """Test simple master/slave WorkChainNodes"""
    aiida_profile.reset_storage()
    master = orm.WorkChainNode()
    slave = orm.WorkChainNode()

    input_1 = orm.Int(3).store()
    input_2 = orm.Int(5).store()
    output_1 = orm.Int(2).store()

    master.base.links.add_incoming(input_1, LinkType.INPUT_WORK, 'input_1')
    slave.base.links.add_incoming(master, LinkType.CALL_WORK, 'CALL')
    slave.base.links.add_incoming(input_2, LinkType.INPUT_WORK, 'input_2')

    master.store()
    slave.store()

    output_1.base.links.add_incoming(master, LinkType.RETURN, 'RETURN')

    master.seal()
    slave.seal()

    uuids_values = [(v.uuid, v.value) for v in (output_1,)]
    filename1 = tmp_path / 'export1.aiida'
    create_archive([output_1], filename=filename1)
    aiida_profile.reset_storage()
    import_archive(filename1)

    for uuid, value in uuids_values:
        assert orm.load_node(uuid).value == value

# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test running a :class:`~aiida.orm.nodes.data.codes.containerized.ContainerizedCode` code."""
from aiida import orm
from aiida.engine import run_get_node


def test_add_singularity():
    """Test installed containerized code by add plugin"""
    builder = orm.load_code('add-singularity@localhost').get_builder()
    builder.x = orm.Int(4)
    builder.y = orm.Int(6)
    builder.metadata.options.resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}

    results, node = run_get_node(builder)

    assert node.is_finished_ok
    assert 'sum' in results
    assert 'remote_folder' in results
    assert 'retrieved' in results
    assert results['sum'].value == 10


def main():
    test_add_singularity()


if __name__ == '__main__':
    main()

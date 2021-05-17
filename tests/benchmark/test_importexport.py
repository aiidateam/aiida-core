# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unused-argument,protected-access
"""Performance benchmark tests for import/export utilities.

The purpose of these tests is to benchmark and compare importing and exporting
parts of the database.
"""
from io import StringIO

import pytest

from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.orm import CalcFunctionNode, Dict, load_node
from aiida.tools.importexport import import_data, export


def recursive_provenance(in_node, depth, breadth, num_objects=0):
    """Recursively build a provenance tree."""
    if not in_node.is_stored:
        in_node.store()
    if depth < 1:
        return
    depth -= 1
    for _ in range(breadth):
        calcfunc = CalcFunctionNode()
        calcfunc.set_process_state(ProcessState.FINISHED)
        calcfunc.set_exit_status(0)
        calcfunc.add_incoming(in_node, link_type=LinkType.INPUT_CALC, link_label='input')
        calcfunc.store()

        out_node = Dict(dict={str(i): i for i in range(10)})
        for idx in range(num_objects):
            out_node.put_object_from_filelike(StringIO('a' * 10000), f'key{str(idx)}')
        out_node.add_incoming(calcfunc, link_type=LinkType.CREATE, link_label='output')
        out_node.store()

        calcfunc.seal()

        recursive_provenance(out_node, depth, breadth, num_objects)


def get_export_kwargs(**kwargs):
    """Return default export keyword arguments."""
    obj = {
        'input_calc_forward': True,
        'input_work_forward': True,
        'create_backward': True,
        'return_backward': True,
        'call_calc_backward': True,
        'call_work_backward': True,
        'include_comments': True,
        'include_logs': True,
        'overwrite': True,
    }
    obj.update(kwargs)
    return obj


TREE = {'no-objects': (4, 3, 0), 'with-objects': (4, 3, 2)}


@pytest.mark.parametrize('depth,breadth,num_objects', TREE.values(), ids=TREE.keys())
@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.benchmark(group='import-export')
def test_export(benchmark, tmp_path, depth, breadth, num_objects):
    """Benchmark exporting a provenance graph."""
    root_node = Dict()
    recursive_provenance(root_node, depth=depth, breadth=breadth, num_objects=num_objects)
    out_path = tmp_path / 'test.aiida'
    kwargs = get_export_kwargs(filename=str(out_path))

    def _setup():
        if out_path.exists():
            out_path.unlink()

    def _run():
        export([root_node], **kwargs)

    benchmark.pedantic(_run, setup=_setup, iterations=1, rounds=12, warmup_rounds=1)
    assert out_path.exists()


@pytest.mark.parametrize('depth,breadth,num_objects', TREE.values(), ids=TREE.keys())
@pytest.mark.benchmark(group='import-export')
def test_import(aiida_profile, benchmark, tmp_path, depth, breadth, num_objects):
    """Benchmark importing a provenance graph."""
    aiida_profile.reset_db()
    root_node = Dict()
    recursive_provenance(root_node, depth=depth, breadth=breadth, num_objects=num_objects)
    root_uuid = root_node.uuid
    out_path = tmp_path / 'test.aiida'
    kwargs = get_export_kwargs(filename=str(out_path))
    export([root_node], **kwargs)

    def _setup():
        aiida_profile.reset_db()

    def _run():
        import_data(str(out_path))

    benchmark.pedantic(_run, setup=_setup, iterations=1, rounds=12, warmup_rounds=1)
    load_node(root_uuid)

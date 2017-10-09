"""Tests for the AiiDA workchain Sphinx directive."""

from os.path import join, dirname

import pytest

WORKCHAIN = join(dirname(__file__), 'workchain_source')


@pytest.mark.parametrize('builder', ['xml', 'html'])
def test_workchain_build(build_sphinx, compare_equal, builder):
    out_dir = build_sphinx(WORKCHAIN, builder=builder)
    index_file = join(out_dir, 'index.' + builder)
    with open(index_file, 'r') as f:
        compare_equal(f.read())

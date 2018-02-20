"""Tests for the AiiDA workchain Sphinx directive."""

from os.path import join, dirname

import pytest

WORKCHAIN = join(dirname(__file__), 'workchain_source')


def test_workchain_build(build_sphinx, xml_equal, reference_result):
    out_dir = build_sphinx(WORKCHAIN)
    index_file = join(out_dir, 'index.xml')
    xml_equal(index_file, reference_result('workchain.xml'))    

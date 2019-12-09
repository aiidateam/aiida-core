# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Pytest fixtures for AiiDA sphinx extension tests."""
import os
import sys
import shutil
import tempfile
import subprocess
import xml.etree.ElementTree as ET

import pytest


@pytest.fixture
def reference_result():
    """Return reference results (for check)."""

    def inner(name):
        return os.path.join(os.path.dirname(__file__), 'reference_results', name)

    return inner


@pytest.fixture
def build_dir():
    """Create directory to build documentation."""
    with tempfile.TemporaryDirectory() as dirpath:
        yield dirpath


@pytest.fixture
def build_sphinx(build_dir):  # pylint: disable=redefined-outer-name
    """Returns function to run sphinx to build documentation."""

    def inner(source_dir, builder='xml'):
        """Run sphinx to build documentation."""
        doctree_dir = os.path.join(build_dir, 'doctrees')
        out_dir = os.path.join(build_dir, builder)

        completed_proc = subprocess.run(
            [sys.executable, '-m', 'sphinx', '-b', builder, '-d', doctree_dir, source_dir, out_dir],
            # add demo_workchain.py to the PYTHONPATH
            cwd=os.path.join(source_dir, os.pardir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return out_dir, completed_proc

    return inner


@pytest.fixture
def xml_equal():
    """Check whether output and reference XML are identical."""

    def inner(test_file, reference_file):
        if not os.path.isfile(reference_file):
            shutil.copyfile(test_file, reference_file)
            raise ValueError('Reference file does not exist!')
        assert _flatten_xml(test_file) == _flatten_xml(reference_file)

    return inner


def _flatten_xml(filename):
    """Flatten XML to list of tuples of tag and dictionary."""
    return [(el.tag, {k: v
                      for k, v in el.attrib.items()
                      if k not in ['source']}, el.text)
            for el in ET.parse(filename).iter()]

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
from pathlib import Path
import sys
import shutil
import xml.etree.ElementTree as ET

from sphinx.testing.path import path as sphinx_path
from sphinx.testing.util import SphinxTestApp
import pytest

SRC_DIR = Path(__file__).parent / 'sources'
WORKCHAIN_DIR = Path(__file__).parent / 'workchains'


@pytest.fixture
def reference_result():
    """Return reference results (for check)."""

    def inner(name):
        return os.path.join(os.path.dirname(__file__), 'reference_results', name)

    return inner


class SphinxBuild:
    """Class for testing sphinx builds"""

    def __init__(self, app: SphinxTestApp, src: Path):
        self.app = app
        self.src = src

    def build(self, assert_pass=True):
        """Build sphinx app.

        :param assert_pass: if True, assert that no warnings are raised during build"""
        try:
            sys.path.append(os.path.abspath(WORKCHAIN_DIR))
            self.app.build()
        finally:
            sys.path.pop()
        if assert_pass:
            assert self.warnings == '', self.status
        return self

    @property
    def status(self):
        return self.app._status.getvalue()  # pylint: disable=protected-access

    @property
    def warnings(self):
        return self.app._warning.getvalue()  # pylint: disable=protected-access

    @property
    def outdir(self):
        return Path(self.app.outdir)


@pytest.fixture
def sphinx_build_factory(make_app, tmp_path):
    """SphinxBuild factory fixture

    Usage::

        def test_wc(sphinx_build_factory):
            ...
            sphinx_build = sphinx_build_factory('workchain', buildername='xml')
            sphinx_build.build(assert_pass=True)
    """

    def _func(src_folder, **kwargs):
        shutil.copytree(SRC_DIR / src_folder, tmp_path / src_folder)
        app = make_app(srcdir=sphinx_path(os.path.abspath((tmp_path / src_folder))), **kwargs)
        return SphinxBuild(app, tmp_path / src_folder)

    yield _func


@pytest.fixture
def xml_equal():
    """Check whether output and reference XML are identical."""

    def inner(test_file, reference_file):
        if not os.path.isfile(reference_file):
            shutil.copyfile(test_file, reference_file)
            raise ValueError('Reference file does not exist!')
        try:
            assert _flatten_xml(test_file) == _flatten_xml(reference_file)
        except AssertionError:
            print(Path(test_file.read_text()))
            raise

    return inner


def _flatten_xml(filename):
    """Flatten XML to list of tuples of tag and dictionary."""
    return [(el.tag, {k: v
                      for k, v in el.attrib.items()
                      if k not in ['source']}, el.text)
            for el in ET.parse(filename).iter()]

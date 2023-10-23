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
import pathlib
import shutil
import sys

import pytest
from sphinx.testing.util import SphinxTestApp

SRC_DIR = pathlib.Path(__file__).parent / 'sources'
WORKCHAIN_DIR = pathlib.Path(__file__).parent / 'workchains'


class SphinxBuild:
    """Class for testing sphinx builds"""

    def __init__(self, app: SphinxTestApp, src: pathlib.Path):
        self.app = app
        self.src = src

    def build(self, assert_pass=True):
        """Build sphinx app.

        :param assert_pass: if True, assert that no warnings are raised during build"""
        try:
            sys.path.append(str(WORKCHAIN_DIR.absolute()))
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
        return pathlib.Path(self.app.outdir)


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
        filepath_source = SRC_DIR / src_folder
        filepath_target = tmp_path / src_folder
        shutil.copytree(filepath_source, filepath_target)
        app = make_app(srcdir=filepath_target.absolute(), **kwargs)
        return SphinxBuild(app, filepath_target)

    yield _func

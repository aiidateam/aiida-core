# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :class:`aiida.orm.nodes.data.code.abstract.AbstractCode` class."""
import pathlib

import pytest

from aiida.orm.nodes.data.code.abstract import AbstractCode


class MockCode(AbstractCode):
    """Implementation of :class:`aiida.orm.nodes.data.code.abstract.AbstractCode`."""

    def can_run_on_computer(self, computer) -> bool:
        """Return whether the code can run on a given computer."""
        return True

    def get_executable(self) -> pathlib.PurePosixPath:
        """Return the executable that the submission script should execute to run the code."""
        return pathlib.PurePosixPath('/bin/executable')

    @property
    def full_label(self) -> str:
        """Return the full label of this code."""
        return ''


def test_set_label():
    """Test the :meth:`aiida.orm.nodes.data.code.abstract.AbstractCode.label` property setter."""
    label = 'some-label'
    code = MockCode(label=label)
    assert code.label == label

    code.label = 'alternate-label'
    assert code.label == 'alternate-label'

    with pytest.raises(ValueError, match=''):
        code.label = 'illegal@label'


def test_constructor_defaults():
    """Test the defaults of the constructor."""
    code = MockCode()
    assert code.default_calc_job_plugin is None
    assert code.append_text == ''
    assert code.prepend_text == ''
    assert code.use_double_quotes is False
    assert code.is_hidden is False

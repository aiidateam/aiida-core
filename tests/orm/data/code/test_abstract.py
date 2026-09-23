###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the abstract :class:`aiida.orm.Code` base class."""

import pathlib

import pytest

from aiida.orm.nodes.data.code.abstract import Code
from aiida.orm.nodes.data.code.containerized import ContainerizedCode
from aiida.orm.nodes.data.code.installed import InstalledCode
from aiida.orm.nodes.data.code.portable import PortableCode
from aiida.orm.nodes.data.code.shell import ShellCode


class MockCode(Code):
    """Implementation of :class:`aiida.orm.nodes.data.code.abstract.Code`."""

    def can_run_on_computer(self, computer) -> bool:
        """Return whether the code can run on a given computer."""
        return True

    def get_executable(self) -> pathlib.PurePath:
        """Return the executable that the submission script should execute to run the code."""
        return pathlib.PurePath('/bin/executable')

    @property
    def full_label(self) -> str:
        """Return the full label of this code."""
        return ''


def test_code_base_class():
    """Test that the concrete code plugins inherit the abstract ``Code`` base."""
    for cls in (InstalledCode, PortableCode, ContainerizedCode, ShellCode, MockCode):
        assert issubclass(cls, Code)

    with pytest.raises(TypeError, match='abstract class'):
        Code()  # type: ignore[abstract]


def test_set_label():
    """Test the :meth:`aiida.orm.nodes.data.code.abstract.Code.label` property setter."""
    label = 'some-label'
    code = MockCode(label=label)
    assert code.label == label

    code.label = 'alternate-label'
    assert code.label == 'alternate-label'

    with pytest.raises(ValueError, match='The label contains a `@` symbol, which is not allowed'):
        code.label = 'illegal@label'


def test_with_mpi():
    """Test the :meth:`aiida.orm.nodes.data.code.abstract.Code.with_mpi` property setter."""
    code = MockCode()
    assert code.with_mpi is None

    for value in (True, False, None):
        code.with_mpi = value
        assert code.with_mpi is value

    with pytest.raises(TypeError):
        code.with_mpi = 'False'


def test_constructor_defaults():
    """Test the defaults of the constructor."""
    code = MockCode()
    assert code.default_calc_job_plugin is None
    assert code.append_text == ''
    assert code.prepend_text == ''
    assert code.use_double_quotes is False
    assert code.is_hidden is False

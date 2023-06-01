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
"""Tests for the :class:`aiida.orm.nodes.data.code.portable.PortableCode` class."""
import io
import pathlib

import pytest

from aiida.common.exceptions import ModificationNotAllowed, ValidationError
from aiida.orm.nodes.data.code.portable import PortableCode


def test_constructor_raises(tmp_path):
    """Test the constructor when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'missing .* required positional argument'):
        PortableCode()  # pylint: disable=no-value-for-parameter

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        PortableCode(filepath_executable=pathlib.Path('/usr/bin/bash'), filepath_files=tmp_path)

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        PortableCode(filepath_executable='bash', filepath_files='string')


def test_constructor(tmp_path):
    """Test the constructor."""
    (tmp_path / 'bash').touch()
    (tmp_path / 'alternate').touch()
    filepath_executable = 'bash'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)
    assert sorted(code.base.repository.list_object_names()) == ['alternate', 'bash']


def test_validate(tmp_path):
    """Test the validator is called before storing."""
    filepath_executable = 'bash'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)

    code.base.attributes.set(code._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, None)  # pylint: disable=protected-access

    with pytest.raises(ValidationError, match='The `filepath_executable` is not set.'):
        code.store()

    code.filepath_executable = filepath_executable

    with pytest.raises(ValidationError, match=r'The executable .* is not one of the uploaded files'):
        code.store()

    code.base.repository.put_object_from_filelike(io.BytesIO(b''), filepath_executable)
    code.store()
    assert code.is_stored


def test_can_run_on_computer(aiida_localhost, tmp_path):
    """Test the :meth:`aiida.orm.nodes.data.code.portable.PortableCode.can_run_on_computer` method."""
    code = PortableCode(filepath_executable='./bash', filepath_files=tmp_path)
    assert code.can_run_on_computer(aiida_localhost)


def test_filepath_executable(tmp_path):
    """Test the :meth:`aiida.orm.nodes.data.code.portable.PortableCode.filepath_executable` property."""
    filepath_executable = 'bash'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)

    with pytest.raises(ValueError, match=r'The `filepath_executable` should not be absolute.'):
        code.filepath_executable = '/usr/bin/cat'

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        code.filepath_executable = pathlib.Path(filepath_executable)

    code.filepath_executable = filepath_executable
    code.base.repository.put_object_from_filelike(io.BytesIO(b''), filepath_executable)
    code.store()

    with pytest.raises(ModificationNotAllowed):
        code.filepath_executable = filepath_executable


def test_full_label(tmp_path):
    """Test the :meth:`aiida.orm.nodes.data.code.portable.PortableCode.full_label` property."""
    label = 'some-label'
    code = PortableCode(label=label, filepath_executable='bash', filepath_files=tmp_path)
    assert code.full_label == label


def test_get_execname(tmp_path):
    """Test the deprecated :meth:`aiida.orm.nodes.data.code.portable.PortableCode.get_execname` method."""
    code = PortableCode(label='some-label', filepath_executable='bash', filepath_files=tmp_path)
    assert code.get_execname() == 'bash'

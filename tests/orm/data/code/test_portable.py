###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.orm.nodes.data.code.portable.PortableCode` class."""

import io
import pathlib

import pytest
from aiida.common.exceptions import ModificationNotAllowed, ValidationError
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm.nodes.data.code.portable import PortableCode


def test_constructor_raises(tmp_path):
    """Test the constructor when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'missing .* required positional argument'):
        PortableCode()

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

    code.base.attributes.set(code._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, None)

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
    with pytest.warns(AiidaDeprecationWarning):
        assert code.get_execname() == 'bash'


def test_portablecode_extra_files(tmp_path, chdir_tmp_path):
    """Test that the node repository contents of an orm.PortableCode are dumped upon YAML export."""
    filepath_files = tmp_path / 'tmp'
    filepath_files.mkdir()
    # (filepath_files / 'bash').touch()
    (filepath_files / 'bash').write_text('bash')
    (filepath_files / 'subdir').mkdir()
    (filepath_files / 'subdir/test').write_text('test')
    code = PortableCode(label='some-label', filepath_executable='bash', filepath_files=filepath_files)
    code.store()
    extra_files = code._prepare_yaml()[1]
    repo_dump_path = tmp_path / code.label
    extra_files_keys = sorted([str(repo_dump_path / _) for _ in ('subdir/test', 'bash')])
    assert sorted(extra_files.keys()) == extra_files_keys
    assert extra_files[str(repo_dump_path / 'bash')] == 'bash'.encode('utf-8')
    assert extra_files[str(repo_dump_path / 'subdir/test')] == 'test'.encode('utf-8')

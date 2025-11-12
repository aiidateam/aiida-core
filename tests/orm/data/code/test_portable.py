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


def test_constructor_raises(tmp_path, bash_path):
    """Test the constructor when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'missing .* required positional argument'):
        PortableCode()

    with pytest.raises(ValueError, match=r'The `filepath_executable` should not be absolute.'):
        PortableCode(filepath_executable=bash_path, filepath_files=tmp_path)

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        PortableCode(filepath_executable=5, filepath_files=tmp_path)

    with pytest.raises(ValueError, match=r'The filepath `string` does not exist.'):
        PortableCode(filepath_executable='bash', filepath_files='string')

    file = tmp_path / 'string'
    file.touch()
    with pytest.raises(ValueError, match=r'The filepath .* is not a directory.'):
        PortableCode(filepath_executable='bash', filepath_files=file)


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
    filepath_executable = 'mycode.py'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)

    with pytest.raises(ValueError, match=r'The `filepath_executable` should not be absolute.'):
        code.filepath_executable = '/usr/bin/cat'

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        code.filepath_executable = 5

    code.filepath_executable = filepath_executable
    code.base.repository.put_object_from_filelike(io.BytesIO(b''), filepath_executable)
    code.store()

    with pytest.raises(ModificationNotAllowed):
        code.filepath_executable = filepath_executable


def test_filepath_executable_dotslash(tmp_path):
    """Test that the executable filepath is correctly prefixed with './' if in the top folder."""
    filepath_executable = 'mycode.py'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)
    code.base.repository.put_object_from_filelike(io.BytesIO(b''), filepath_executable)
    code.store()
    # ./ is prepended
    assert code.get_executable_cmdline_params() == ['./mycode.py']


def test_filepath_executable_dotslash_alreadythere(tmp_path):
    """Test that the executable filepath is not duplicated with './' if already there."""
    filepath_executable = './mycode.py'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)
    code.base.repository.put_object_from_filelike(io.BytesIO(b''), filepath_executable)
    code.store()
    # ./ is not duplicated if already there
    assert code.get_executable_cmdline_params() == ['./mycode.py']


def test_filepath_executable_dotslash_subfolder(tmp_path):
    """Test that the executable filepath is not prefixed with './' if in a subfolder."""
    filepath_executable = 'a/mycode.py'
    code = PortableCode(filepath_executable=filepath_executable, filepath_files=tmp_path)
    code.base.repository.put_object_from_filelike(io.BytesIO(b''), filepath_executable)
    code.store()

    # No ./ needed for a subfolder
    assert code.get_executable_cmdline_params() == ['a/mycode.py']


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
    (filepath_files / 'bash').write_text('bash')
    (filepath_files / 'subdir').mkdir()
    (filepath_files / 'subdir/test').write_text('test')
    code = PortableCode(label='some-label', filepath_executable='bash', filepath_files=filepath_files)
    code.store()
    result, extra_args = code._prepare_yaml()
    ref_result = f"""label: some-label
description: ''
default_calc_job_plugin: null
use_double_quotes: false
with_mpi: null
prepend_text: ''
append_text: ''
filepath_executable: bash
filepath_files: {tmp_path}/some-label
"""

    assert extra_args == {}
    assert result.decode() == ref_result
    repo_dump_path = tmp_path / code.label
    # In this case portablecode takes care of the dumping
    dumped_files = {f.relative_to(repo_dump_path) for f in repo_dump_path.rglob('*')}
    inserted_files = {f.relative_to(filepath_files) for f in filepath_files.rglob('*')}
    assert dumped_files == inserted_files


def test_serialization(tmp_path, chdir_tmp_path):
    """Test that the node repository contents of an orm.PortableCode are dumped upon YAML export."""
    filepath_files = tmp_path / 'tmp'
    filepath_files.mkdir()
    (filepath_files / 'bash').write_text('bash')
    (filepath_files / 'subdir').mkdir()
    (filepath_files / 'subdir/test').write_text('test')
    code = PortableCode(label='some-label', filepath_executable='bash', filepath_files=filepath_files)
    PortableCode.from_serialized(code.serialize(unstored=True))

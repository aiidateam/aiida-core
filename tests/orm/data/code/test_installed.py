###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.orm.nodes.data.code.installed.InstalledCode` class."""

import pathlib

import pytest

from aiida.common.exceptions import ModificationNotAllowed, ValidationError
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm import Computer
from aiida.orm.nodes.data.code.installed import InstalledCode


def test_constructor_raises(aiida_localhost, bash_path):
    """Test the constructor when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'missing .* required positional arguments'):
        InstalledCode()

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        InstalledCode(computer=aiida_localhost, filepath_executable=bash_path)

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        InstalledCode(computer='computer', filepath_executable='/usr/bin/bash')


def test_constructor(aiida_localhost, bash_path):
    """Test the constructor."""
    filepath_executable = str(bash_path.absolute())
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)
    assert code.computer.pk == aiida_localhost.pk
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)


def test_validate(aiida_localhost, bash_path):
    """Test the validator is called before storing."""
    filepath_executable = str(bash_path.absolute())
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)

    code.computer = aiida_localhost
    code.base.attributes.set(code._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, None)

    with pytest.raises(ValidationError, match='The `filepath_executable` is not set.'):
        code.store()

    code.filepath_executable = filepath_executable
    code.store()
    assert code.is_stored


def test_can_run_on_computer(aiida_localhost, bash_path):
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.can_run_on_computer` method."""
    code = InstalledCode(computer=aiida_localhost, filepath_executable=str(bash_path.absolute()))
    computer = Computer()

    assert code.can_run_on_computer(aiida_localhost)
    assert not code.can_run_on_computer(computer)


def test_filepath_executable(aiida_localhost, bash_path, cat_path):
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.filepath_executable` property."""
    filepath_executable = str(bash_path.absolute())
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)

    # Relative path
    filepath_executable = 'bash'
    code = InstalledCode(computer=aiida_localhost, filepath_executable=filepath_executable)
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)

    # Change through the property
    filepath_executable = str(cat_path.absolute())
    code.filepath_executable = filepath_executable
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        code.filepath_executable = pathlib.Path(filepath_executable)

    code.store()

    with pytest.raises(ModificationNotAllowed):
        code.filepath_executable = filepath_executable


@pytest.fixture
def computer(request, aiida_computer_local, aiida_computer_ssh):
    """Return a computer configured for ``core.local`` and ``core.ssh`` transport."""
    if request.param == 'core.local':
        return aiida_computer_local(configure=False)

    if request.param == 'core.ssh':
        return aiida_computer_ssh(configure=False)

    raise ValueError(f'unsupported request parameter: {request.param}')


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('computer', ('core.local', 'core.ssh'), indirect=True)
def test_validate_filepath_executable(ssh_key, computer, bash_path, tmp_path):
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.validate_filepath_executable` method."""

    filepath_executable = '/usr/bin/not-existing'
    dummy_executable = tmp_path / 'dummy.sh'
    # Default Linux permissions are 664, so file is not executable
    dummy_executable.touch()
    code = InstalledCode(computer=computer, filepath_executable=filepath_executable)
    dummy_code = InstalledCode(computer=computer, filepath_executable=str(dummy_executable))

    with pytest.raises(ValidationError, match=r'Could not connect to the configured computer.*'):
        code.validate_filepath_executable()

    if computer.transport_type == 'core.ssh':
        computer.configure(key_filename=str(ssh_key), key_policy='AutoAddPolicy')
    else:
        computer.configure()

    with pytest.raises(ValidationError, match=r'The provided remote absolute path .* does not exist on the computer\.'):
        code.validate_filepath_executable()

    with pytest.raises(
        ValidationError,
        match=r'The file at the remote absolute path .* exists, but might not actually be executable\.',
    ):
        # Didn't put this in the if, using transport.put, as we anyway only connect to localhost via SSH in this test
        dummy_code.validate_filepath_executable()

    code.filepath_executable = str(bash_path.absolute())
    code.validate_filepath_executable()


def test_full_label(aiida_localhost, bash_path):
    """Test the :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.full_label` property."""
    label = 'some-label'
    code = InstalledCode(label=label, computer=aiida_localhost, filepath_executable=str(bash_path.absolute()))
    assert code.full_label == f'{label}@{aiida_localhost.label}'


def test_get_execname(aiida_localhost, bash_path):
    """Test the deprecated :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.get_execname` method."""
    code = InstalledCode(label='some-label', computer=aiida_localhost, filepath_executable=str(bash_path.absolute()))
    with pytest.warns(AiidaDeprecationWarning):
        assert code.get_execname() == str(bash_path.absolute())


def test_serialization(aiida_localhost, bash_path):
    """Test the deprecated :meth:`aiida.orm.nodes.data.code.installed.InstalledCode.get_execname` method."""
    code = InstalledCode(label='some-label', computer=aiida_localhost, filepath_executable=str(bash_path.absolute()))

    InstalledCode.from_serialized(**code.serialize())

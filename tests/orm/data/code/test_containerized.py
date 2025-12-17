###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.orm.nodes.data.code.containerized.ContainerizedCode` class."""

import pathlib

import pytest

from aiida.orm.nodes.data.code.containerized import ContainerizedCode


def test_constructor_raises(aiida_localhost):
    """Test the constructor when it is supposed to raise."""
    with pytest.raises(ValueError, match=r'Both `engine_command` and `image_name` must be provided.'):
        ContainerizedCode(engine_command='bash')

    with pytest.raises(ValueError, match=r'Both `engine_command` and `image_name` must be provided.'):
        ContainerizedCode(image_name='img')

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        path = pathlib.Path('bash')
        ContainerizedCode(computer=aiida_localhost, filepath_executable=path, engine_command='docker', image_name='img')

    with pytest.raises(TypeError, match=r'Got object of type .*'):
        ContainerizedCode(computer='computer', filepath_executable='bash', engine_command='docker', image_name='img')

    with pytest.raises(ValueError, match="the '{image_name}' template field should be in engine command."):
        ContainerizedCode(computer=aiida_localhost, filepath_executable='ls', engine_command='docker', image_name='img')


def test_constructor(aiida_localhost):
    """Test the constructor."""
    image_name = 'image'
    engine_command = 'docker {image_name}'
    filepath_executable = 'bash'

    code = ContainerizedCode(
        computer=aiida_localhost,
        image_name=image_name,
        engine_command=engine_command,
        filepath_executable=filepath_executable,
    )
    assert code.computer.pk == aiida_localhost.pk
    assert code.filepath_executable == pathlib.PurePath(filepath_executable)
    assert code.wrap_cmdline_params is False


def test_wrap_cmdline_params(aiida_localhost):
    """Test the ``wrap_cmdline_params`` keyword and property."""
    image_name = 'image'
    engine_command = 'docker {image_name}'
    filepath_executable = 'bash'

    code = ContainerizedCode(
        computer=aiida_localhost,
        image_name=image_name,
        engine_command=engine_command,
        filepath_executable=filepath_executable,
        wrap_cmdline_params=True,
    )
    assert code.wrap_cmdline_params is True

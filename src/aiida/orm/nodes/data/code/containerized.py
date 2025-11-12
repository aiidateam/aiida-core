###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin representing an executable code inside a container.

The containerized code allows specifying a container image and the executable filepath within that container that is to
be executed when a calculation job is run with this code.
"""

from __future__ import annotations

import pathlib

from aiida.common.lang import type_check
from aiida.common.pydantic import MetadataField

from .installed import InstalledCode, InstalledCodeModel

__all__ = ('ContainerizedCode',)


class ContainerizedCodeModel(InstalledCodeModel):
    """Model describing required information to create an instance."""

    engine_command: str = MetadataField(
        ...,
        title='Engine command',
        description='The command to run the container. It must contain the placeholder {image_name} that will be '
        'replaced with the `image_name`.',
        short_name='-E',
        priority=3,
    )
    image_name: str = MetadataField(
        ...,
        title='Image name',
        description='Name of the image container in which to the run the executable.',
        short_name='-I',
        priority=2,
    )
    wrap_cmdline_params: bool = MetadataField(
        False,
        title='Wrap command line parameters',
        description='Whether all command line parameters to be passed to the engine command should be wrapped in '
        'a double quotes to form a single argument. This should be set to `True` for Docker.',
        priority=1,
    )


class ContainerizedCode(InstalledCode):
    """Data plugin representing an executable code in container on a remote computer."""

    Model = ContainerizedCodeModel

    _KEY_ATTRIBUTE_ENGINE_COMMAND: str = 'engine_command'
    _KEY_ATTRIBUTE_IMAGE_NAME: str = 'image_name'

    def __init__(self, engine_command: str, image_name: str, **kwargs):
        super().__init__(**kwargs)
        self.engine_command = engine_command
        self.image_name = image_name

    @property
    def filepath_executable(self) -> pathlib.PurePath:
        """Return the filepath of the executable that this code represents.

        .. note:: This is overridden from the base class since the path does not have to be absolute.

        :return: The filepath of the executable.
        """
        return super().filepath_executable

    @filepath_executable.setter
    def filepath_executable(self, value: str) -> None:
        """Set the filepath of the executable that this code represents.

        .. note:: This is overridden from the base class since the path does not have to be absolute.

        :param value: The filepath of the executable.
        """
        type_check(value, str)
        self.base.attributes.set(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, value)

    @property
    def engine_command(self) -> str:
        """Return the engine command with image as template field of the containerized code.

        :return: The engine command of the containerized code
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_ENGINE_COMMAND)

    @engine_command.setter
    def engine_command(self, value: str) -> None:
        """Set the engine command of the containerized code.

        :param value: The engine command of the containerized code
        """
        type_check(value, str)

        if '{image_name}' not in value:
            raise ValueError("the '{image_name}' template field should be in engine command.")

        self.base.attributes.set(self._KEY_ATTRIBUTE_ENGINE_COMMAND, value)

    @property
    def image_name(self) -> str:
        """The image name of container.

        :return: The image name of container.
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_IMAGE_NAME)

    @image_name.setter
    def image_name(self, value: str) -> None:
        """Set the image name of container.

        :param value: The image name of container.
        """
        type_check(value, str)
        self.base.attributes.set(self._KEY_ATTRIBUTE_IMAGE_NAME, value)

    def get_prepend_cmdline_params(
        self, mpi_args: list[str] | None = None, extra_mpirun_params: list[str] | None = None
    ) -> list[str]:
        """Return the list of prepend cmdline params for mpi seeting

        :return: list of prepend cmdline parameters.
        """
        engine_cmdline = self.engine_command.format(image_name=self.image_name)
        engine_cmdline_params = engine_cmdline.split()

        return (mpi_args or []) + (extra_mpirun_params or []) + engine_cmdline_params

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

import typing as t

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm.cli import CliFieldInfo
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.code.installed import InstalledCode

__all__ = ('ContainerizedCode',)


class ContainerizedCode(InstalledCode):
    """Data plugin representing an executable code in container on a remote computer."""

    _KEY_ATTRIBUTE_ENGINE_COMMAND: str = 'engine_command'
    _KEY_ATTRIBUTE_IMAGE_NAME: str = 'image_name'

    def __init__(
        self,
        engine_command: str | None = None,
        image_name: str | None = None,
        **kwargs: t.Any,
    ):
        if engine_command is None or image_name is None:
            raise ValueError('Both `engine_command` and `image_name` must be provided.')

        super().__init__(**kwargs)

        if '{image_name}' not in engine_command:
            raise ValueError("the '{image_name}' template field should be in engine command")

        self.engine_command = engine_command
        self.image_name = image_name

    @attribute(
        cli_field_info=CliFieldInfo(
            help='The command to run the container. It must contain the placeholder {image_name} that will be '
            'replaced with the `image_name`',
            short_name='-E',
        )
    )
    def engine_command(self) -> str:
        """The engine command with image as template field of the containerized code."""
        return self.base.attributes.get(self._KEY_ATTRIBUTE_ENGINE_COMMAND)

    @engine_command.setter
    def engine_command(self, value: str) -> None:
        type_check(value, str)

        if '{image_name}' not in value:
            raise exceptions.ValidationError("`engine_command` must contain the '{image_name}' template field.")

        self.base.attributes.set(self._KEY_ATTRIBUTE_ENGINE_COMMAND, value)

    @attribute(
        cli_field_info=CliFieldInfo(
            help='Name of the image in which to the run the executable',
            short_name='-I',
        )
    )
    def image_name(self) -> str:
        """The image name of container."""
        return self.base.attributes.get(self._KEY_ATTRIBUTE_IMAGE_NAME)

    @image_name.setter
    def image_name(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self._KEY_ATTRIBUTE_IMAGE_NAME, value)

    def get_prepend_cmdline_params(
        self,
        mpi_args: list[str] | None = None,
        extra_mpirun_params: list[str] | None = None,
    ) -> list[str]:
        """Return the list of prepend cmdline params for mpi seeting

        :return: list of prepend cmdline parameters.
        """
        engine_cmdline = self.engine_command.format(image_name=self.image_name)
        engine_cmdline_params = engine_cmdline.split()

        return (mpi_args or []) + (extra_mpirun_params or []) + engine_cmdline_params

    def _validate(self) -> None:
        super()._validate()

        try:
            engine_command = self.engine_command
        except AttributeError as exc:
            raise exceptions.ValidationError('`engine_command` is not set.') from exc

        try:
            self.image_name
        except AttributeError as exc:
            raise exceptions.ValidationError('`image_name` is not set.') from exc

        if '{image_name}' not in engine_command:
            raise exceptions.ValidationError("`engine_command` must contain the '{image_name}' template field.")

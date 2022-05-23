# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin representing an executable code on a remote computer.

This plugin should be used if an executable is pre-installed on a computer. The ``InstalledCode`` represents the code by
storing the absolute filepath of the relevant executable and the computer on which it is installed. The computer is
represented by an instance of :class:`aiida.orm.computers.Computer`. Each time a :class:`aiida.engine.CalcJob` is run
using an ``InstalledCode``, it will run its executable on the associated computer.
"""
from glob import escape
import pathlib

import click

from aiida.cmdline.params.types import ComputerParamType
from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.common.log import override_log_level
from aiida.orm import Computer

from .abstract import AbstractCode

__all__ = ('ContainerizedCode',)


class ContainerizedCode(AbstractCode):
    """Data plugin representing an executable code on a remote computer."""

    _KEY_ATTRIBUTE_FILEPATH_EXECUTABLE: str = 'filepath_executable'
    _KEY_ATTRIBUTE_ENGINE_COMMAND: str = 'engine_command'
    _KEY_ATTRIBUTE_IMAGE: str = 'image'
    _KEY_ATTRIBUTE_ESCAPE_EXEC_LINE: str = 'escape_exec_line'

    def __init__(
        self, 
        filepath_executable: str, 
        engine_command: str, 
        image: str,
        computer: Computer,# TODO: can be None for Portable
        escape_exec_line: bool=False,   
        **kwargs):
        """Construct a new instance.

        :param computer: The remote computer on which the executable is located.
        :param filepath_executable: The absolute filepath of the executable on the remote computer.
        """
        super().__init__(**kwargs)
        self.computer = computer
        self.filepath_executable = filepath_executable
        self.engine_command = engine_command
        self.image = image
        self.escape_exec_line = escape_exec_line

    def _validate(self):
        """Validate the instance by checking that a computer has been defined.

        :raises :class:`aiida.common.exceptions.ValidationError`: If the state of the node is invalid.
        """
        super()._validate()

        if not self.computer:
            raise exceptions.ValidationError('The `computer` is undefined.')

        # TODO more validate for image, engine_command, escape_exec_line
        try:
            self.filepath_executable
        except TypeError as exception:
            raise exceptions.ValidationError('The `filepath_executable` is not set.') from exception

    def validate_filepath_executable(self):
        """Validate the ``filepath_executable`` attribute.

        Checks whether the executable exists on the remote computer if a transport can be opened to it. This method
        is intentionally not called in ``_validate`` as to allow the creation of ``Code`` instances whose computers can
        not yet be connected to and as to not require the overhead of opening transports in storing a new code.

        :raises `~aiida.common.exceptions.ValidationError`: if no transport could be opened or if the defined executable
            does not exist on the remote computer.
        """
        # TODO: check docker, singularity, sarus can be found from path
        try:
            with override_log_level():  # Temporarily suppress noisy logging
                with self.computer.get_transport() as transport:
                    file_exists = transport.isfile(self.filepath_executable)
        except Exception:  # pylint: disable=broad-except
            raise exceptions.ValidationError(
                'Could not connect to the configured computer to determine whether the specified executable exists.'
            )

        if not file_exists:
            raise exceptions.ValidationError(
                f'The provided remote absolute path `{self.filepath_executable}` does not exist on the computer.'
            )

    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        :param computer: The computer.
        :return: ``True`` if the provided computer is the same as the one configured for this code.
        """
        type_check(computer, Computer)
        return computer.pk == self.computer.pk

    def get_executable(self) -> str:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """
        return self.filepath_executable
    
    @property
    def engine_command(self) -> str:
        """
        doc
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_ENGINE_COMMAND)

    @engine_command.setter
    def engine_command(self, value: str) -> None:
        """
        doc
        """
        type_check(value, str)
        
        # TODO: check contain image template
        
        self.base.attributes.set(self._KEY_ATTRIBUTE_ENGINE_COMMAND, value)
        
    @property
    def escape_exec_line(self) -> str:
        """
        doc
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_ESCAPE_EXEC_LINE)

    @escape_exec_line.setter
    def escape_exec_line(self, value: bool) -> None:
        """
        doc
        """
        type_check(value, bool)
        
        # TODO: check contain image template
        
        self.base.attributes.set(self._KEY_ATTRIBUTE_ESCAPE_EXEC_LINE, value)
        
    @property
    def image(self) -> str:
        """
        doc
        """
        return self.base.attributes.get(self._KEY_ATTRIBUTE_IMAGE)

    @image.setter
    def image(self, value: str) -> None:
        """
        doc
        """
        type_check(value, str)
        
        # TODO: check contain image template
        
        self.base.attributes.set(self._KEY_ATTRIBUTE_IMAGE, value)
        
    def get_engine_command(self) -> str:
        cmdline = self.engine_command.format(image=self.image)

        return cmdline.split()
        
    @property
    def full_label(self) -> str:
        """Return the full label of this code.

        The full label can be just the label itself but it can be something else. However, it at the very least has to
        include the label of the code.

        :return: The full label of the code.
        """
        return f'{self.label}@{self.computer.label}'

    @property
    def filepath_executable(self) -> pathlib.PurePath:
        """Return the absolute filepath of the executable that this code represents.

        :return: The absolute filepath of the executable.
        """
        return pathlib.PurePath(self.base.attributes.get(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE))

    @filepath_executable.setter
    def filepath_executable(self, value: str) -> None:
        """Set the absolute filepath of the executable that this code represents.

        :param value: The absolute filepath of the executable.
        """
        type_check(value, str)

        if not pathlib.PurePath(value).is_absolute():
            raise ValueError('the `filepath_executable` should be absolute.')

        self.base.attributes.set(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, value)

    @staticmethod
    def cli_validate_label_uniqueness(ctx, _, value):
        """Validate the uniqueness of the label of the code."""
        from aiida.orm import load_code

        computer = ctx.params.get('computer', None)

        if computer is None:
            return value

        full_label = f'{value}@{computer.label}'

        try:
            load_code(full_label)
        except exceptions.NotExistent:
            pass
        except exceptions.MultipleObjectsError:
            raise click.BadParameter(f'Multiple codes with the label `{full_label}` already exist.')
        else:
            raise click.BadParameter(f'A code with the label `{full_label}` already exists.')

        return value

    @classmethod
    def _get_cli_options(cls) -> dict:
        """Return the CLI options that would allow to create an instance of this class."""
        options = {
            'computer': {
                'required': True,
                'prompt': 'Computer',
                'help': 'The remote computer on which the executable resides.',
                'type': ComputerParamType(),
            },
            'filepath_executable': {
                'required': True,
                'type': click.Path(exists=False),
                'prompt': 'Absolute filepath executable',
                'help': 'Absolute filepath of the executable on the remote computer.',
            }
        }
        options.update(**super()._get_cli_options())

        return options

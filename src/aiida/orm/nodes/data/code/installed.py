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

from __future__ import annotations

import pathlib
from typing import cast

from pydantic import field_validator

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.common.log import override_log_level
from aiida.common.pydantic import MetadataField
from aiida.orm import Computer
from aiida.orm.entities import from_backend_entity

from .abstract import AbstractCode
from .legacy import Code

__all__ = ('InstalledCode',)


class InstalledCode(Code):
    """Data plugin representing an executable code on a remote computer."""

    _EMIT_CODE_DEPRECATION_WARNING: bool = False
    _KEY_ATTRIBUTE_FILEPATH_EXECUTABLE: str = 'filepath_executable'
    _SKIP_MODEL_INHERITANCE_CHECK: bool = True

    class Model(AbstractCode.Model):
        """Model describing required information to create an instance."""

        computer: str = MetadataField(
            title='Computer',
            description='The label of the remote computer on which the executable resides.',
            orm_to_model=lambda node: cast(InstalledCode, node).computer.label,
            model_to_orm=lambda model: cast(InstalledCode.Model, model).load_computer(),
            short_name='-Y',
            priority=2,
        )
        filepath_executable: str = MetadataField(
            title='Filepath executable',
            description='Filepath of the executable on the remote computer.',
            orm_to_model=lambda node: str(cast(InstalledCode, node).filepath_executable),
            short_name='-X',
            priority=1,
        )

        @field_validator('computer', mode='before')
        @classmethod
        def validate_computer(cls, value: str | int) -> str:
            """Validate the ``computer`` field.

            :param value: The value to validate.
            :return: The validated value.
            :raises ValueError: If the value is not a string or integer.
            """
            from aiida.orm import load_computer

            if isinstance(value, int):
                try:
                    return load_computer(value).label
                except exceptions.NotExistent as exception:
                    raise ValueError(f'No computer found for the given id: {value}') from exception
            return value

    def __init__(self, computer: Computer, filepath_executable: str, **kwargs):
        """Construct a new instance.

        :param computer: The remote computer on which the executable is located.
        :param filepath_executable: The absolute filepath of the executable on the remote computer.
        """
        super().__init__(**kwargs)
        self.computer = computer
        self.filepath_executable = filepath_executable

    def _validate(self):
        """Validate the instance by checking that a computer has been defined.

        :raises :class:`aiida.common.exceptions.ValidationError`: If the state of the node is invalid.
        """
        super(Code, self)._validate()  # Change to ``super()._validate()`` once deprecated ``Code`` class is removed.

        if not self.computer:  # type: ignore[truthy-bool]
            raise exceptions.ValidationError('The `computer` is undefined.')

        try:
            self.filepath_executable
        except TypeError as exception:
            raise exceptions.ValidationError('The `filepath_executable` is not set.') from exception

    def validate_filepath_executable(self):
        """Validate the ``filepath_executable`` attribute.

        Checks whether the executable exists on the remote computer if a transport can be opened to it. This method
        is intentionally not called in ``_validate`` as to allow the creation of ``Code`` instances whose computers can
        not yet be connected to and as to not require the overhead of opening transports in storing a new code.

        .. note:: If the ``filepath_executable`` is not an absolute path, the check is skipped.

        :raises `~aiida.common.exceptions.ValidationError`: if no transport could be opened or if the defined executable
            does not exist on the remote computer.
        """
        if not self.filepath_executable.is_absolute():
            return

        try:
            with override_log_level():  # Temporarily suppress noisy logging
                with self.computer.get_transport() as transport:
                    file_exists = transport.isfile(str(self.filepath_executable))
                    if file_exists:
                        mode = transport.get_mode(str(self.filepath_executable))
                        # `format(mode, 'b')` with default permissions
                        # gives 110110100, representing rw-rw-r--
                        # Check on index 2 if user has execute
                        user_has_execute = format(mode, 'b')[2] == '1'

        except Exception as exception:
            raise exceptions.ValidationError(
                'Could not connect to the configured computer to determine whether the specified executable exists.'
            ) from exception

        if not file_exists:
            raise exceptions.ValidationError(
                f'The provided remote absolute path `{self.filepath_executable}` does not exist on the computer.'
            )

        if not user_has_execute:
            execute_msg = (
                f'The file at the remote absolute path `{self.filepath_executable}` exists, '
                'but might not actually be executable. Check the permissions.'
            )
            raise exceptions.ValidationError(execute_msg)

    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        :param computer: The computer.
        :return: ``True`` if the provided computer is the same as the one configured for this code.
        """
        type_check(computer, Computer)
        return computer.pk == self.computer.pk

    def get_executable(self) -> pathlib.PurePath:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """
        return self.filepath_executable

    @property
    def computer(self) -> Computer:
        """Return the computer of this code."""
        assert self.backend_entity.computer is not None
        return from_backend_entity(Computer, self.backend_entity.computer)

    @computer.setter
    def computer(self, computer: Computer) -> None:
        """Set the computer of this code.

        :param computer: A `Computer`.
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the computer on a stored node')

        type_check(computer, Computer, allow_none=False)
        self.backend_entity.computer = computer.backend_entity

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
        self.base.attributes.set(self._KEY_ATTRIBUTE_FILEPATH_EXECUTABLE, value)

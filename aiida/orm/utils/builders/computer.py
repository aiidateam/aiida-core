# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Manage computer objects with lazy loading of the db env"""
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import ValidationError
from aiida.common.utils import ErrorAccumulator


class ComputerBuilder:  # pylint: disable=too-many-instance-attributes
    """Build a computer with validation of attribute combinations"""

    @staticmethod
    def from_computer(computer):
        """Create ComputerBuilder from existing computer instance.

        See also :py:func:`~ComputerBuilder.get_computer_spec`"""
        spec = ComputerBuilder.get_computer_spec(computer)
        return ComputerBuilder(**spec)

    @staticmethod
    def get_computer_spec(computer):
        """Get computer attributes from existing computer instance.

        These attributes can be used to create a new ComputerBuilder::

            spec = ComputerBuilder.get_computer_spec(old_computer)
            builder = ComputerBuilder(**spec)
            new_computer = builder.new()"""
        spec = {}
        spec['label'] = computer.label
        spec['description'] = computer.description
        spec['hostname'] = computer.hostname
        spec['scheduler'] = computer.scheduler_type
        spec['transport'] = computer.transport_type
        spec['use_double_quotes'] = computer.get_use_double_quotes()
        spec['prepend_text'] = computer.get_prepend_text()
        spec['append_text'] = computer.get_append_text()
        spec['work_dir'] = computer.get_workdir()
        spec['shebang'] = computer.get_shebang()
        spec['mpirun_command'] = ' '.join(computer.get_mpirun_command())
        spec['mpiprocs_per_machine'] = computer.get_default_mpiprocs_per_machine()
        spec['default_memory_per_machine'] = computer.get_default_memory_per_machine()

        return spec

    def __init__(self, **kwargs):
        self._computer_spec = {}
        self._err_acc = ErrorAccumulator(self.ComputerValidationError)

        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def validate(self, raise_error=True):
        """Validate the computer options."""
        return self._err_acc.result(raise_error=self.ComputerValidationError if raise_error else False)

    @with_dbenv()
    def new(self):
        """Build and return a new computer instance (not stored)"""
        from aiida.orm import Computer

        self.validate()

        # Will be used at the end to check if all keys are known
        passed_keys = set(self._computer_spec.keys())
        used = set()

        computer = Computer(label=self._get_and_count('label', used), hostname=self._get_and_count('hostname', used))

        computer.description = self._get_and_count('description', used)
        computer.scheduler_type = self._get_and_count('scheduler', used)
        computer.transport_type = self._get_and_count('transport', used)
        computer.set_use_double_quotes(self._get_and_count('use_double_quotes', used))
        computer.set_prepend_text(self._get_and_count('prepend_text', used))
        computer.set_append_text(self._get_and_count('append_text', used))
        computer.set_workdir(self._get_and_count('work_dir', used))
        computer.set_shebang(self._get_and_count('shebang', used))

        mpiprocs_per_machine = self._get_and_count('mpiprocs_per_machine', used)
        # In the command line, 0 means unspecified
        if mpiprocs_per_machine == 0:
            mpiprocs_per_machine = None
        if mpiprocs_per_machine is not None:
            try:
                mpiprocs_per_machine = int(mpiprocs_per_machine)
            except ValueError:
                raise self.ComputerValidationError(
                    'Invalid value provided for mpiprocs_per_machine, '
                    'must be a valid integer'
                )
            if mpiprocs_per_machine <= 0:
                raise self.ComputerValidationError(
                    'Invalid value provided for mpiprocs_per_machine, '
                    'must be positive'
                )
            computer.set_default_mpiprocs_per_machine(mpiprocs_per_machine)

        def_memory_per_machine = self._get_and_count('default_memory_per_machine', used)
        if def_memory_per_machine is not None:
            try:
                def_memory_per_machine = int(def_memory_per_machine)
            except ValueError:
                raise self.ComputerValidationError(
                    'Invalid value provided for memory_per_machine, must be a valid integer'
                )
            try:
                computer.set_default_memory_per_machine(def_memory_per_machine)
            except ValidationError as exception:
                raise self.ComputerValidationError(f'Invalid value for `default_memory_per_machine`: {exception}')

        mpirun_command_internal = self._get_and_count('mpirun_command', used).strip().split(' ')
        if mpirun_command_internal == ['']:
            mpirun_command_internal = []
        computer._mpirun_command_validator(mpirun_command_internal)  # pylint: disable=protected-access
        computer.set_mpirun_command(mpirun_command_internal)

        # Complain if there are keys that are passed but not used
        if passed_keys - used:
            raise self.ComputerValidationError(
                f"Unknown parameters passed to the ComputerBuilder: {', '.join(sorted(passed_keys - used))}"
            )

        return computer

    def __getattr__(self, key):
        """Access computer attributes used to build the computer"""
        if not key.startswith('_'):
            try:
                return self._computer_spec[key]
            except KeyError:
                raise self.ComputerValidationError(f'{key} not set')
        return None

    def _get(self, key):
        """
        Return a spec, or None if not defined

        :param key: name of a computer spec"""
        return self._computer_spec.get(key)

    def _get_and_count(self, key, used):
        """
        Return a spec, or raise if not defined.
        Moreover, add the key to the 'used' dict.

        :param key: name of a computer spec
        :param used: should be a set of keys that you want to track.
           ``key`` will be added to this set if the value exists in the spec and can be retrieved.
        """
        retval = self.__getattr__(key)
        # I first get a retval, so if I get an exception, I don't add it to the 'used' set
        used.add(key)
        return retval

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            self._set_computer_attr(key, value)
        super().__setattr__(key, value)

    def _set_computer_attr(self, key, value):
        """Set a computer attribute if it passes validation."""
        backup = self._computer_spec.copy()
        self._computer_spec[key] = value
        success, _ = self.validate(raise_error=False)
        if not success:
            self._computer_spec = backup
            self.validate()

    class ComputerValidationError(Exception):
        """
        A ComputerBuilder instance may raise this

         * when asked to instanciate a code with missing or invalid computer attributes
         * when asked for a computer attibute that has not been set yet."""

        def __init__(self, msg):
            super().__init__()
            self.msg = msg

        def __str__(self):
            return self.msg

        def __repr__(self):
            return f'<ComputerValidationError: {self}>'

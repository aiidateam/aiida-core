###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for Computer entities"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Tuple, Type, Union
from uuid import UUID

from pydantic import field_serializer

from aiida.common import exceptions
from aiida.common.log import AIIDA_LOGGER, AiidaLoggerType
from aiida.common.pydantic import MetadataField
from aiida.manage import get_manager
from aiida.plugins import SchedulerFactory, TransportFactory

from . import entities, users

if TYPE_CHECKING:
    from aiida.orm import AuthInfo, User
    from aiida.orm.implementation import BackendComputer, StorageBackend
    from aiida.schedulers import Scheduler
    from aiida.transports import Transport

__all__ = ('Computer',)


class ComputerCollection(entities.Collection['Computer']):
    """The collection of Computer entries."""

    collection_type: ClassVar[str] = 'computers'

    @staticmethod
    def _entity_base_cls() -> Type[Computer]:
        return Computer

    def get_or_create(self, label: str, **kwargs: Any) -> Tuple[bool, Computer]:
        """Try to retrieve a Computer from the DB with the given arguments;
        create (and store) a new Computer if such a Computer was not present yet.

        :param label: computer label

        :return: (computer, created) where computer is the computer (new or existing,
            in any case already stored) and created is a boolean saying
        """
        if not label:
            raise ValueError('Computer label must be provided')

        try:
            return False, self.get(label=label)
        except exceptions.NotExistent:
            return True, Computer(backend=self.backend, label=label, **kwargs)

    def list_labels(self) -> list[tuple[str]]:
        """Return a list with all the labels of the computers in the DB."""
        return self._backend.computers.list_names()

    def delete(self, pk: int) -> None:
        """Delete the computer with the given id"""
        return self._backend.computers.delete(pk)


class Computer(entities.Entity['BackendComputer', ComputerCollection]):
    """Computer entity."""

    _logger = AIIDA_LOGGER.getChild('orm.computers')

    PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL = 'minimum_scheduler_poll_interval'
    PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT = 10.0
    PROPERTY_WORKDIR = 'workdir'
    PROPERTY_SHEBANG = 'shebang'

    _CLS_COLLECTION = ComputerCollection

    class Model(entities.Entity.Model):
        uuid: UUID = MetadataField(
            description='The UUID of the computer',
            read_only=True,
            examples=['123e4567-e89b-12d3-a456-426614174000'],
        )
        label: str = MetadataField(
            description='Label for the computer',
            examples=['localhost'],
        )
        description: str = MetadataField(
            '',
            description='Description of the computer',
            examples=['My local machine'],
        )
        hostname: str = MetadataField(
            description='Hostname of the computer',
            examples=['localhost'],
        )
        transport_type: str = MetadataField(
            description='Transport type of the computer',
            examples=['core.local'],
        )
        scheduler_type: str = MetadataField(
            description='Scheduler type of the computer',
            examples=['core.direct'],
        )
        metadata: Dict[str, Any] = MetadataField(
            default_factory=dict,
            description='Metadata of the computer',
            may_be_large=True,
            examples=[{'key': 'value'}],
        )

        @field_serializer('uuid')
        def serialize_uuid(self, value: UUID) -> str:
            """Serialize UUID to string."""
            return str(value)

    def __init__(
        self,
        label: Optional[str] = None,
        hostname: str = '',
        description: str = '',
        transport_type: str = '',
        scheduler_type: str = '',
        workdir: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        backend: Optional['StorageBackend'] = None,
    ) -> None:
        """Construct a new computer."""
        backend = backend or get_manager().get_profile_storage()
        model = backend.computers.create(
            label=label,
            hostname=hostname,
            description=description,
            transport_type=transport_type,
            scheduler_type=scheduler_type,
            metadata=metadata,
        )
        super().__init__(model)
        if workdir is not None:
            self.set_workdir(workdir)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self!s}>'

    def __str__(self) -> str:
        return f'{self.label} ({self.hostname}), pk: {self.pk}'

    @property
    def uuid(self) -> str:
        """Return the UUID for this computer.

        This identifier is unique across all entities types and backend instances.

        :return: the entity uuid
        """
        return self._backend_entity.uuid

    @property
    def logger(self) -> AiidaLoggerType:
        return self._logger

    @classmethod
    def _label_validator(cls, label: str) -> None:
        """Validates the label."""
        if not label.strip():
            raise exceptions.ValidationError('No label specified')

    @classmethod
    def _hostname_validator(cls, hostname: str) -> None:
        """Validates the hostname."""
        if not (hostname or hostname.strip()):
            raise exceptions.ValidationError('No hostname specified')

    @classmethod
    def _description_validator(cls, description: str) -> None:
        """Validates the description."""
        # The description is always valid

    @classmethod
    def _transport_type_validator(cls, transport_type: str) -> None:
        """Validates the transport string."""
        from aiida.plugins.entry_point import get_entry_point_names

        if transport_type not in get_entry_point_names('aiida.transports'):
            raise exceptions.ValidationError('The specified transport is not a valid one')

    @classmethod
    def _scheduler_type_validator(cls, scheduler_type: str) -> None:
        """Validates the transport string."""
        from aiida.plugins.entry_point import get_entry_point_names

        if scheduler_type not in get_entry_point_names('aiida.schedulers'):
            raise exceptions.ValidationError(f'The specified scheduler `{scheduler_type}` is not a valid one')

    @classmethod
    def _prepend_text_validator(cls, prepend_text: str) -> None:
        """Validates the prepend text string."""
        # no validation done

    @classmethod
    def _append_text_validator(cls, append_text: str) -> None:
        """Validates the append text string."""
        # no validation done

    @classmethod
    def _workdir_validator(cls, workdir: str) -> None:
        """Validates the transport string."""
        if not workdir.strip():
            raise exceptions.ValidationError('No workdir specified')

        try:
            convertedwd = workdir.format(username='test')
        except KeyError as exc:
            raise exceptions.ValidationError(f'In workdir there is an unknown replacement field {exc.args[0]}')
        except ValueError as exc:
            raise exceptions.ValidationError(f"Error in the string: '{exc}'")

        if not os.path.isabs(convertedwd):
            raise exceptions.ValidationError('The workdir must be an absolute path')

    def _mpirun_command_validator(self, mpirun_cmd: Union[List[str], Tuple[str, ...]]) -> None:
        """Validates the mpirun_command variable. MUST be called after properly
        checking for a valid scheduler.
        """
        if not isinstance(mpirun_cmd, (tuple, list)) or not all(isinstance(i, str) for i in mpirun_cmd):  # type: ignore[redundant-expr]
            raise exceptions.ValidationError('the mpirun_command must be a list of strings')

        try:
            job_resource_keys = self.get_scheduler().job_resource_class.get_valid_keys()
        except exceptions.EntryPointError:
            raise exceptions.ValidationError('Unable to load the scheduler for this computer')

        subst = {i: 'value' for i in job_resource_keys}
        subst['tot_num_mpiprocs'] = 'value'

        try:
            for arg in mpirun_cmd:
                arg.format(**subst)
        except KeyError as exc:
            raise exceptions.ValidationError(f'In workdir there is an unknown replacement field {exc.args[0]}')
        except ValueError as exc:
            raise exceptions.ValidationError(f"Error in the string: '{exc}'")

    def validate(self) -> None:
        """Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr and similar methods
        that automatically read either from the DB or from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super().validate() method first!
        """
        if not self.label.strip():
            raise exceptions.ValidationError('No name specified')

        self._label_validator(self.label)
        self._hostname_validator(self.hostname)
        self._description_validator(self.description)
        self._transport_type_validator(self.transport_type)
        self._scheduler_type_validator(self.scheduler_type)
        self._workdir_validator(self.get_workdir())
        self.default_memory_per_machine_validator(self.get_default_memory_per_machine())

        try:
            mpirun_cmd = self.get_mpirun_command()
        except exceptions.DbContentError:
            raise exceptions.ValidationError('Error in the DB content of the metadata')

        # To be called AFTER the validation of the scheduler
        self._mpirun_command_validator(mpirun_cmd)

    @classmethod
    def _default_mpiprocs_per_machine_validator(cls, def_cpus_per_machine: Optional[int]) -> None:
        """Validates the default number of CPUs per machine (node)"""
        if def_cpus_per_machine is None:
            return

        if not isinstance(def_cpus_per_machine, int) or def_cpus_per_machine <= 0:  # type: ignore[redundant-expr]
            raise exceptions.ValidationError(
                'Invalid value for default_mpiprocs_per_machine, must be a positive integer, or an empty string if you '
                'do not want to provide a default value.'
            )

    @classmethod
    def default_memory_per_machine_validator(cls, def_memory_per_machine: Optional[int]) -> None:
        """Validates the default amount of memory (kB) per machine (node)"""
        if def_memory_per_machine is None:
            return

        if not isinstance(def_memory_per_machine, int) or def_memory_per_machine <= 0:  # type: ignore[redundant-expr]
            raise exceptions.ValidationError(
                f'Invalid value for def_memory_per_machine, must be a positive int, got: {def_memory_per_machine}'
            )

    def copy(self) -> Computer:
        """Return a copy of the current object to work with, not stored yet."""
        return entities.from_backend_entity(Computer, self._backend_entity.copy())

    def store(self) -> Computer:
        """Store the computer in the DB.

        Differently from Nodes, a computer can be re-stored if its properties
        are to be changed (e.g. a new mpirun command, etc.)
        """
        self.validate()
        return super().store()

    @property
    def label(self) -> str:
        """Return the computer label.

        :return: the label.
        """
        return self._backend_entity.label

    @label.setter
    def label(self, value: str) -> None:
        """Set the computer label.

        :param value: the label to set.
        """
        self._backend_entity.set_label(value)

    @property
    def description(self) -> str:
        """Return the computer computer.

        :return: the description.
        """
        return self._backend_entity.description

    @description.setter
    def description(self, value: str) -> None:
        """Set the computer description.

        :param value: the description to set.
        """
        self._backend_entity.set_description(value)

    @property
    def hostname(self) -> str:
        """Return the computer hostname.

        :return: the hostname.
        """
        return self._backend_entity.hostname

    @hostname.setter
    def hostname(self, value: str) -> None:
        """Set the computer hostname.

        :param value: the hostname to set.
        """
        self._backend_entity.set_hostname(value)

    @property
    def scheduler_type(self) -> str:
        """Return the computer scheduler type.

        :return: the scheduler type.
        """
        return self._backend_entity.get_scheduler_type()

    @scheduler_type.setter
    def scheduler_type(self, value: str) -> None:
        """Set the computer scheduler type.

        :param value: the scheduler type to set.
        """
        self._backend_entity.set_scheduler_type(value)

    @property
    def transport_type(self) -> str:
        """Return the computer transport type.

        :return: the transport_type.
        """
        return self._backend_entity.get_transport_type()

    @transport_type.setter
    def transport_type(self, value: str) -> None:
        """Set the computer transport type.

        :param value: the transport_type to set.
        """
        self._backend_entity.set_transport_type(value)

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return the computer metadata.

        :return: the metadata.
        """
        return self._backend_entity.get_metadata()

    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """Set the computer metadata.

        :param value: the metadata to set.
        """
        self._backend_entity.set_metadata(value)

    def delete_property(self, name: str, raise_exception: bool = True) -> None:
        """Delete a property from this computer

        :param name: the name of the property
        :param raise_exception: if True raise if the property does not exist, otherwise return None
        """
        olddata = self.metadata
        try:
            del olddata[name]
            self.metadata = olddata
        except KeyError:
            if raise_exception:
                raise AttributeError(f"'{name}' property not found")

    def set_property(self, name: str, value: Any) -> None:
        """Set a property on this computer

        :param name: the property name
        :param value: the new value
        """
        metadata = self.metadata or {}
        metadata[name] = value
        self.metadata = metadata

    def get_property(self, name: str, *args: Any) -> Any:
        """Get a property of this computer

        :param name: the property name
        :param args: additional arguments

        :return: the property value
        """
        if len(args) > 1:
            raise TypeError('get_property expected at most 2 arguments')
        olddata = self.metadata
        try:
            return olddata[name]
        except KeyError:
            if not args:
                raise AttributeError(f"'{name}' property not found")
            return args[0]

    def get_prepend_text(self) -> str:
        return self.get_property('prepend_text', '')

    def set_prepend_text(self, val: str) -> None:
        self.set_property('prepend_text', str(val))

    def get_append_text(self) -> str:
        return self.get_property('append_text', '')

    def set_append_text(self, val: str) -> None:
        self.set_property('append_text', str(val))

    def get_use_double_quotes(self) -> bool:
        """Return whether the command line parameters of this computer should be escaped with double quotes.

        :returns: True if to escape with double quotes, False otherwise which is also the default.
        """
        return self.get_property('use_double_quotes', False)

    def set_use_double_quotes(self, val: bool) -> None:
        """Set whether the command line parameters of this computer should be escaped with double quotes.

        :param use_double_quotes: True if to escape with double quotes, False otherwise.
        """
        from aiida.common.lang import type_check

        type_check(val, bool)
        self.set_property('use_double_quotes', val)

    def get_mpirun_command(self) -> List[str]:
        """Return the mpirun command. Must be a list of strings, that will be
        then joined with spaces when submitting.

        I also provide a sensible default that may be ok in many cases.
        """
        return self.get_property('mpirun_command', ['mpirun', '-np', '{tot_num_mpiprocs}'])

    def set_mpirun_command(self, val: Union[List[str], Tuple[str, ...]]) -> None:
        """Set the mpirun command. It must be a list of strings (you can use
        string.split() if you have a single, space-separated string).
        """
        if not isinstance(val, (tuple, list)) or not all(isinstance(i, str) for i in val):  # type: ignore[redundant-expr]
            raise TypeError('the mpirun_command must be a list of strings')
        self.set_property('mpirun_command', val)

    def get_default_mpiprocs_per_machine(self) -> Optional[int]:
        """Return the default number of CPUs per machine (node) for this computer,
        or None if it was not set.
        """
        return self.get_property('default_mpiprocs_per_machine', None)

    def set_default_mpiprocs_per_machine(self, def_cpus_per_machine: Optional[int]) -> None:
        """Set the default number of CPUs per machine (node) for this computer.
        Accepts None if you do not want to set this value.
        """
        if def_cpus_per_machine is None:
            self.delete_property('default_mpiprocs_per_machine', raise_exception=False)
        elif not isinstance(def_cpus_per_machine, int):
            raise TypeError('def_cpus_per_machine must be an integer (or None)')
        self.set_property('default_mpiprocs_per_machine', def_cpus_per_machine)

    def get_default_memory_per_machine(self) -> Optional[int]:
        """Return the default amount of memory (kB) per machine (node) for this computer,
        or None if it was not set.
        """
        return self.get_property('default_memory_per_machine', None)

    def set_default_memory_per_machine(self, def_memory_per_machine: Optional[int]) -> None:
        """Set the default amount of memory (kB) per machine (node) for this computer.
        Accepts None if you do not want to set this value.
        """
        self.default_memory_per_machine_validator(def_memory_per_machine)
        self.set_property('default_memory_per_machine', def_memory_per_machine)

    def get_minimum_job_poll_interval(self) -> float:
        """Get the minimum interval between subsequent requests to poll the scheduler for job status.

        .. note:: If no value was ever set for this computer it will fall back on the default provided by the associated
            transport class in the ``DEFAULT_MINIMUM_JOB_POLL_INTERVAL`` attribute. If the computer doesn't have a
            transport class, or it cannot be loaded, or it doesn't provide a job poll interval default, then this will
            fall back on the ``PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT`` attribute of this class.

        :return: The minimum interval (in seconds).
        """
        try:
            default = self.get_transport_class().DEFAULT_MINIMUM_JOB_POLL_INTERVAL
        except (exceptions.ConfigurationError, AttributeError):
            default = self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT

        return self.get_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, default)

    def set_minimum_job_poll_interval(self, interval: float) -> None:
        """Set the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        :param interval: The minimum interval in seconds
        """
        self.set_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, interval)

    def get_workdir(self) -> str:
        """Get the working directory for this computer
        :return: The currently configured working directory
        """
        return self.get_property(self.PROPERTY_WORKDIR, '/scratch/{username}/aiida_run/')

    def set_workdir(self, val: str) -> None:
        self.set_property(self.PROPERTY_WORKDIR, val)

    def get_shebang(self) -> str:
        return self.get_property(self.PROPERTY_SHEBANG, '#!/bin/bash')

    def set_shebang(self, val: str) -> None:
        """:param str val: A valid shebang line"""
        if not isinstance(val, str):
            raise ValueError(f'{val} is invalid. Input has to be a string')
        if not val.startswith('#!'):
            raise ValueError(f'{val} is invalid. A shebang line has to start with #!')
        metadata = self.metadata
        metadata['shebang'] = val
        self.metadata = metadata

    def get_authinfo(self, user: 'User') -> 'AuthInfo':
        """Return the aiida.orm.authinfo.AuthInfo instance for the
        given user on this computer, if the computer
        is configured for the given user.

        :param user: a User instance.
        :return: a AuthInfo instance
        :raise aiida.common.NotExistent: if the computer is not configured for the given
            user.
        """
        from . import authinfos

        try:
            authinfo = authinfos.AuthInfo.get_collection(self.backend).get(dbcomputer_id=self.pk, aiidauser_id=user.pk)
        except exceptions.NotExistent as exc:
            raise exceptions.NotExistent(
                f'Computer `{self.label}` (ID={self.pk}) not configured for user `{user.get_short_name()}` '
                f'(ID={user.pk}) - use `verdi computer configure` first'
            ) from exc

        return authinfo

    @property
    def is_configured(self) -> bool:
        """Return whether the computer is configured for the current default user.

        :return: Boolean, ``True`` if the computer is configured for the current default user, ``False`` otherwise.
        """
        user = users.User.get_collection(self.backend).get_default()
        assert user is not None
        return self.is_user_configured(user)

    def is_user_configured(self, user: 'User') -> bool:
        """Is the user configured on this computer?

        :param user: the user to check
        :return: True if configured, False otherwise
        """
        try:
            self.get_authinfo(user)
            return True
        except exceptions.NotExistent:
            return False

    def is_user_enabled(self, user: 'User') -> bool:
        """Is the given user enabled to run on this computer?

        :param user: the user to check
        :return: True if enabled, False otherwise
        """
        try:
            authinfo = self.get_authinfo(user)
            return authinfo.enabled
        except exceptions.NotExistent:
            # Return False if the user is not configured (in a sense, it is disabled for that user)
            return False

    def get_transport(self, user: Optional['User'] = None) -> 'Transport':
        """Return a Transport class, configured with all correct parameters.
        The Transport is closed (meaning that if you want to run any operation with
        it, you have to open it first (i.e., e.g. for a SSH transport, you have
        to open a connection). To do this you can call ``transport.open()``, or simply
        run within a ``with`` statement::

           transport = Computer.get_transport()
           with transport:
               print(transport.whoami())

        :param user: if None, try to obtain a transport for the default user.
            Otherwise, pass a valid User.

        :return: a (closed) Transport, already configured with the connection
            parameters to the supercomputer, as configured with ``verdi computer configure``
            for the user specified as a parameter ``user``.
        """
        from . import authinfos

        user = user or users.User.get_collection(self.backend).get_default()
        assert user is not None
        authinfo = authinfos.AuthInfo.get_collection(self.backend).get(dbcomputer=self, aiidauser=user)
        return authinfo.get_transport()

    def get_transport_class(self) -> Type['Transport']:
        """Get the transport class for this computer.  Can be used to instantiate a transport instance."""
        try:
            return TransportFactory(self.transport_type)
        except exceptions.EntryPointError as exception:
            raise exceptions.ConfigurationError(
                f'No transport found for {self.label} [type {self.transport_type}], message: {exception}'
            )

    def get_scheduler(self) -> 'Scheduler':
        """Get a scheduler instance for this computer"""
        try:
            scheduler_class = SchedulerFactory(self.scheduler_type)
            # I call the init without any parameter
            return scheduler_class()
        except exceptions.EntryPointError as exception:
            raise exceptions.ConfigurationError(
                f'No scheduler found for {self.label} [type {self.scheduler_type}], message: {exception}'
            )

    def configure(self, user: Optional['User'] = None, **kwargs: Any) -> 'AuthInfo':
        """Configure a computer for a user with valid auth params passed via kwargs

        :param user: the user to configure the computer for
        :kwargs: the configuration keywords with corresponding values
        :return: the authinfo object for the configured user
        """
        from . import authinfos

        transport_cls = self.get_transport_class()
        user = user or users.User.get_collection(self.backend).get_default()
        assert user is not None
        valid_keys = set(transport_cls.get_valid_auth_params())

        if not set(kwargs.keys()).issubset(valid_keys):
            invalid_keys = [key for key in kwargs if key not in valid_keys]
            raise ValueError(f'{transport_cls}: received invalid authentication parameter(s) "{invalid_keys}"')

        try:
            authinfo = self.get_authinfo(user)
        except exceptions.NotExistent:
            authinfo = authinfos.AuthInfo(self, user, backend=self.backend)

        auth_params = authinfo.get_auth_params()

        if valid_keys:
            auth_params.update(kwargs)
            authinfo.set_auth_params(auth_params)
            authinfo.store()

        return authinfo

    def get_configuration(self, user: Optional['User'] = None) -> Dict[str, Any]:
        """Get the configuration of computer for the given user as a dictionary

        :param user: the user to to get the configuration for, otherwise default user
        """
        user = user or users.User.get_collection(self.backend).get_default()
        assert user is not None

        try:
            authinfo = self.get_authinfo(user)
        except exceptions.NotExistent:
            return {}

        return authinfo.get_auth_params()

# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for Computer entities"""
import logging
import os
import warnings

from aiida import transports, schedulers
from aiida.common import exceptions
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.manage.manager import get_manager
from aiida.plugins import SchedulerFactory, TransportFactory

from . import entities
from . import users

__all__ = ('Computer',)


def validate_work_dir(_, value):
    """Validate the transport string."""
    if not value.strip():
        raise exceptions.ValidationError('No work_dir specified')

    try:
        convertedwd = value.format(username='test')
    except KeyError as exc:
        raise exceptions.ValidationError('In work_dir there is an unknown replacement field {}'.format(exc.args[0]))
    except ValueError as exc:
        raise exceptions.ValidationError("Error in the string: '{}'".format(exc))

    if not os.path.isabs(convertedwd):
        raise exceptions.ValidationError('The work_dir must be an absolute path')


def validate_mpirun_command(computer, value):
    """Validate the mpirun_command variable, MUST be called after properly checking for a valid scheduler."""
    if not isinstance(value, (tuple, list)) or not all(isinstance(i, str) for i in value):
        raise exceptions.ValidationError('the mpirun_command must be a list of strings')

    try:
        job_resource_keys = computer.get_scheduler().job_resource_class.get_valid_keys()
    except exceptions.EntryPointError:
        raise exceptions.ValidationError('Unable to load the scheduler for this computer')

    subst = {i: 'value' for i in job_resource_keys}
    subst['tot_num_mpiprocs'] = 'value'

    try:
        for arg in value:
            arg.format(**subst)
    except KeyError as exc:
        raise exceptions.ValidationError('In workdir there is an unknown replacement field {}'.format(exc.args[0]))
    except ValueError as exc:
        raise exceptions.ValidationError("Error in the string: '{}'".format(exc))


def validate_default_mpiprocs_per_machine(_, value):  # pylint: disable=invalid-name
    """Validate the default number of CPUs per machine (node)."""
    if value is None:
        return

    if not isinstance(value, int) or value <= 0:
        raise exceptions.ValidationError(
            'Invalid value for default_mpiprocs_per_machine, must be a positive integer, or an empty string if you do '
            'not want to provide a default value.'
        )


def validate_shebang(_, value):
    """Validate the shebang string."""
    if not isinstance(value, str):
        raise ValueError('{} is invalid. Input has to be a string'.format(value))
    if not value.startswith('#!'):
        raise ValueError('{} is invalid. A shebang line has to start with #!'.format(value))


class Computer(entities.Entity):
    """Class to represent a computer on which calculations are run."""
    # pylint: disable=too-many-public-methods

    _logger = logging.getLogger(__name__)

    PROPERTY_WORK_DIR = 'workdir'
    PROPERTY_SHEBANG = 'shebang'
    PROPERTY_MPI_RUN_COMMAND = 'mpirun_command'
    PROPERTY_MPI_PROCES_PER_MACHINE = 'default_mpiprocs_per_machine'
    PROPERTY_PREPEND_TEXT = 'prepend_text'
    PROPERTY_APPEND_TEXT = 'append_text'
    PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL = 'minimum_scheduler_poll_interval'  # pylint: disable=invalid-name

    _property_mapping = {
        'label': ('label', None, None, None),
        'description': ('description', None, None, None),
        'hostname': ('hostname', None, None, None),
        'transport_type': ('transport', None, None, None),
        'scheduler_type': ('scheduler', None, None, None),
        'shebang': ('shebang', PROPERTY_SHEBANG, '#!/bin/bash', validate_shebang),
        'work_dir': ('work_dir', PROPERTY_WORK_DIR, '/scratch/{username}/aiida_run/', validate_work_dir),
        'mpirun_command':
        ('mpirun_command', PROPERTY_MPI_RUN_COMMAND, ['mpirun', '-np', '{tot_num_mpiprocs}'], validate_mpirun_command),
        'default_mpiprocs_per_machine':
        ('default_mpiprocs_per_machine', PROPERTY_MPI_PROCES_PER_MACHINE, None, validate_default_mpiprocs_per_machine),
        'prepend_text': ('prepend_text', PROPERTY_PREPEND_TEXT, '', None),
        'append_text': ('append_text', PROPERTY_APPEND_TEXT, '', None),
        'minimum_job_poll_interval': ('minimum_job_poll_interval', PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, 10, None),
    }

    class Collection(entities.Collection):
        """The collection of Computer entries."""

        def list_names(self):
            """Return a list with all the names of the computers in the DB."""
            return self._backend.computers.list_names()

        def delete(self, id):  # pylint: disable=redefined-builtin,invalid-name
            """Delete the computer with the given id"""
            return self._backend.computers.delete(id)

    def __init__(
        self, name, hostname, description='', transport_type='', scheduler_type='', workdir=None, backend=None
    ):
        """Construct a new computer.

        :type name: str
        :type hostname: str
        :type description: str
        :type transport_type: str
        :type scheduler_type: str
        :type workdir: str
        :type backend: :class:`aiida.orm.implementation.Backend`

        :rtype: :class:`aiida.orm.Computer`
        """
        # pylint: disable=too-many-arguments
        backend = backend or get_manager().get_backend()
        model = backend.computers.create(
            name=name,
            hostname=hostname,
            description=description,
            transport_type=transport_type,
            scheduler_type=scheduler_type
        )
        super().__init__(model)

        if workdir is not None:
            self.set_property('work_dir', workdir)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{} ({}), pk: {}'.format(self.label, self.hostname, self.pk)

    def copy(self):
        """Return a copy of the current object to work with, not stored yet."""
        return Computer.from_backend_entity(self._backend_entity.copy())

    @property
    def logger(self):
        return self._logger

    @property
    def label(self):
        """Return the computer label.

        :return: the label
        """
        return self._backend_entity.name

    @label.setter
    def label(self, value):
        """Set the computer label.

        :param value: the label
        """
        if not value.strip():
            raise exceptions.ValidationError('invalid label')

        self._backend_entity.set_name(value)

    @property
    def description(self):
        """Return the description of the computer.

        :return: the description
        :rtype: str
        """
        return self._backend_entity.description

    @description.setter
    def description(self, value):
        """Set the computer description.

        :param value: the description
        """
        self._backend_entity.set_description(value)

    @property
    def hostname(self):
        return self._backend_entity.hostname

    @hostname.setter
    def hostname(self, value):
        """Set the computer hostname.

        :param value: the hostname
        """
        if not value.strip():
            raise exceptions.ValidationError('invalid hostname')

        self._backend_entity.set_hostname(value)

    @property
    def scheduler_type(self):
        return self._backend_entity.get_scheduler_type()

    @scheduler_type.setter
    def scheduler_type(self, value):
        """Set the computer scheduler type.

        :param value: the scheduler type
        """
        if value not in schedulers.Scheduler.get_valid_schedulers():
            raise exceptions.ValidationError('the specified scheduler is invalid')

        self._backend_entity.set_scheduler_type(value)

    @property
    def transport_type(self):
        return self._backend_entity.get_transport_type()

    @transport_type.setter
    def transport_type(self, value):
        """Set the computer transport type.

        :param value: the transport type
        """
        if value not in transports.Transport.get_valid_transports():
            raise exceptions.ValidationError('the specified transport is invalid')

        self._backend_entity.set_transport_type(value)

    def get_metadata(self):
        return self._backend_entity.get_metadata()

    def set_metadata(self, metadata):
        """Set the metadata."""
        self._backend_entity.set_metadata(metadata)

    def get_properties(self):
        """Return a dictionary of all computer properties.

        :return: mapping of properties
        """
        properties = {}

        for name, property_tuple in self._property_mapping.items():
            if property_tuple[1] is None:
                properties[property_tuple[0]] = getattr(self, name)
            else:
                prop = self.get_property(property_tuple[1], property_tuple[2])
                if name == 'mpirun_command':
                    prop = ' '.join(prop)
                properties[property_tuple[0]] = prop

        return properties

    def get_property(self, name, default=None):
        """Return a property of this computer.

        :param name: the property name
        :type name: str

        :param default: optional default

        :return: the property value
        """
        try:
            return self.get_metadata()[name]
        except KeyError:
            if default is None:
                return self._property_mapping[name][2]
            return default

    def set_property(self, name, value):
        """Set a property for this computer.

        :param name: the property name
        :param value: the new value
        """
        try:
            _, _, _, validator = self._property_mapping[name]
        except KeyError:
            raise AttributeError("unknown property '{}'".format(name))

        if validator:
            validator(self, value)

        metadata = self.get_metadata() or {}
        metadata[name] = value
        self.set_metadata(metadata)

    def delete_property(self, name, raise_exception=True):
        """Delete a property from this computer.

        :param name: the name of the property
        :type name: str

        :param raise_exception: if True raise if the property does not exist, otherwise return None
        :type raise_exception: bool
        """
        metadata = self.get_metadata()
        try:
            del metadata[name]
        except KeyError:
            if raise_exception:
                raise AttributeError("unknown property '{}'".format(name))
        self.set_metadata(metadata)

    def get_transport(self, user=None):
        """
        Return a Transport class, configured with all correct parameters.
        The Transport is closed (meaning that if you want to run any operation with
        it, you have to open it first (i.e., e.g. for a SSH transport, you have
        to open a connection). To do this you can call ``transports.open()``, or simply
        run within a ``with`` statement::

           transport = Computer.get_transport()
           with transport:
               print(transports.whoami())

        :param user: if None, try to obtain a transport for the default user.
            Otherwise, pass a valid User.

        :return: a (closed) Transport, already configured with the connection
            parameters to the supercomputer, as configured with ``verdi computer configure``
            for the user specified as a parameter ``user``.
        """
        from . import authinfos  # pylint: disable=cyclic-import

        user = user or users.User.objects(self.backend).get_default()
        authinfo = authinfos.AuthInfo.objects(self.backend).get(dbcomputer=self, aiidauser=user)
        return authinfo.get_transport()

    def get_authinfo(self, user):
        """Return the `aiida.orm.authinfo.AuthInfo` instance for the given user on this computer if it exists.

        :param user: a User instance.
        :return: a AuthInfo instance
        :raise aiida.common.NotExistent: if the computer is not configured for the given user.
        """
        from . import authinfos
        return authinfos.AuthInfo.objects(self.backend).get(dbcomputer_id=self.id, aiidauser_id=user.id)

    def is_user_configured(self, user):
        """Return whether the computer is configured for the given user.

        :param user: the user to check
        :return: True if configured, False otherwise
        :rtype: bool
        """
        try:
            self.get_authinfo(user)
            return True
        except exceptions.NotExistent:
            return False

    def is_user_enabled(self, user):
        """Return whether the computer is enabled or the given user.

        :param user: the user to check
        :return: True if enabled, False otherwise
        :rtype: bool
        """
        try:
            authinfo = self.get_authinfo(user)
            return authinfo.enabled
        except exceptions.NotExistent:
            # Return False if the user is not configured (in a sense it is disabled for that user)
            return False

    def get_transport_class(self):
        """Return the transport class for this computer.

        :return: the transport class
        :rtype: :class:`aiida.transports.Transport`
        """
        return TransportFactory(self.transport_type)

    def get_scheduler(self):
        """Return a scheduler instance for this computer.

        :return: the scheduler instance
        :rtype: :class:`aiida.schedulers.Scheduler`
        """
        return SchedulerFactory(self.scheduler_type)()

    def configure(self, user=None, **kwargs):
        """
        Configure a computer for a user with valid auth params passed via kwargs

        :param user: the user to configure the computer for
        :kwargs: the configuration keywords with corresponding values
        :return: the authinfo object for the configured user
        :rtype: :class:`aiida.orm.AuthInfo`
        """
        from . import authinfos

        transport_cls = self.get_transport_class()
        user = user or users.User.objects(self.backend).get_default()
        valid_keys = set(transport_cls.get_valid_auth_params())

        if not set(kwargs.keys()).issubset(valid_keys):
            invalid_keys = [key for key in kwargs if key not in valid_keys]
            raise ValueError(
                '{transport}: received invalid authentication parameter(s) "{invalid}"'.format(
                    transport=transport_cls, invalid=invalid_keys
                )
            )

        try:
            authinfo = self.get_authinfo(user)
        except exceptions.NotExistent:
            authinfo = authinfos.AuthInfo(self, user)

        auth_params = authinfo.get_auth_params()

        if valid_keys:
            auth_params.update(kwargs)
            authinfo.set_auth_params(auth_params)
            authinfo.store()

        return authinfo

    def get_configuration(self, user=None):
        """
        Get the configuration of computer for the given user as a dictionary

        :param user: the user to to get the configuration for.  Uses default user if `None`
        :type user: :class:`aiida.orm.User`
        """

        backend = self.backend
        user = user or users.User.objects(self.backend).get_default()

        config = {}
        try:
            authinfo = backend.authinfos.get(self, user)
            config = authinfo.get_auth_params()
        except exceptions.NotExistent:
            pass

        return config

    @property
    def full_text_info(self):
        """
        Return a (multiline) string with a human-readable detailed information on this computer.

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`.

        :rtype: str
        """
        ret_lines = []
        ret_lines.append('Computer name:     {}'.format(self.name))
        ret_lines.append(' * PK:             {}'.format(self.pk))
        ret_lines.append(' * UUID:           {}'.format(self.uuid))
        ret_lines.append(' * Description:    {}'.format(self.description))
        ret_lines.append(' * Hostname:       {}'.format(self.hostname))
        ret_lines.append(' * Transport type: {}'.format(self.transport))
        ret_lines.append(' * Scheduler type: {}'.format(self.scheduler))
        ret_lines.append(' * Work directory: {}'.format(self.get_property('work_dir')))
        ret_lines.append(' * Shebang:        {}'.format(self.get_property('shebang')))
        ret_lines.append(' * mpirun command: {}'.format(' '.join(self.get_property('mpirun_command'))))
        def_cpus_machine = self.get_property('default_mpiprocs_per_machine')
        if def_cpus_machine is not None:
            ret_lines.append(' * Default number of cpus per machine: {}'.format(def_cpus_machine))
        # pylint: disable=fixme
        # TODO: Put back following line when we port Node to new backend system
        # ret_lines.append(" * Used by:        {} nodes".format(len(self._dbcomputer.dbnodes.all())))

        ret_lines.append(' * prepend text:')
        if self.get_property('prepend_text').strip():
            for line in self.get_property('prepend_text').split('\n'):
                ret_lines.append('   {}'.format(line))
        else:
            ret_lines.append('   # No prepend text.')
        ret_lines.append(' * append text:')
        if self.get_property('append_text').strip():
            for line in self.get_property('append_text').split('\n'):
                ret_lines.append('   {}'.format(line))
        else:
            ret_lines.append('   # No append text.')

        return '\n'.join(ret_lines)

    @property
    def name(self):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.label` property instead.
        """
        return self._backend_entity.name

    def get_name(self):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.label` property instead.
        """
        return self._backend_entity.get_name()

    def set_name(self, val):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.label` property instead.
        """
        self._backend_entity.set_name(val)

    def get_hostname(self):
        """
        Get this computer hostname

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.hostname` property instead.

        :rtype: str
        """
        return self._backend_entity.hostname

    def set_hostname(self, val):
        """
        Set the hostname of this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.hostname` property instead.

        :param val: The new hostname
        :type val: str
        """
        self._backend_entity.set_hostname(val)

    def get_description(self):
        """
        Get the description for this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.description` property instead.

        :return: the description
        :rtype: str
        """

    def set_description(self, val):
        """
        Set the description for this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.description` property instead.

        :param val: the new description
        :type val: str
        """
        self._backend_entity.set_description(val)

    def get_mpirun_command(self):
        """
        Return the mpirun command. Must be a list of strings, that will be
        then joined with spaces when submitting.

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('mpirun_command')` instead.

        I also provide a sensible default that may be ok in many cases.
        """
        return self.get_property('mpirun_command', ['mpirun', '-np', '{tot_num_mpiprocs}'])

    def set_mpirun_command(self, val):
        """
        Set the mpirun command. It must be a list of strings (you can use
        string.split() if you have a single, space-separated string).

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('mpirun_command', value)` instead.
        """
        if not isinstance(val, (tuple, list)) or not all(isinstance(i, str) for i in val):
            raise TypeError('the mpirun_command must be a list of strings')
        self.set_property('mpirun_command', val)

    def get_scheduler_type(self):
        """
        Get the scheduler type for this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.scheduler` property instead.

        :return: the scheduler type
        :rtype: str
        """
        return self._backend_entity.scheduler

    def set_scheduler_type(self, scheduler_type):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.scheduler` property instead.

        :param scheduler_type: the new scheduler type
        """
        self._scheduler_type_validator(scheduler_type)
        self._backend_entity.set_scheduler_type(scheduler_type)

    def get_transport_type(self):
        """
        Get the current transport type for this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.transport` property instead.

        :return: the transport type
        :rtype: str
        """
        return self._backend_entity.transport

    def set_transport_type(self, transport_type):
        """
        Set the transport type for this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.transport` property instead.

        :param transport_type: the new transport type
        :type transport_type: str
        """
        self._backend_entity.set_transport_type(transport_type)

    def get_default_mpiprocs_per_machine(self):
        """
        Return the default number of CPUs per machine (node) for this computer,
        or None if it was not set.

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('default_mpiprocs_per_machine')` instead.

        """
        return self.get_property('default_mpiprocs_per_machine', None)

    def set_default_mpiprocs_per_machine(self, def_cpus_per_machine):
        """
        Set the default number of CPUs per machine (node) for this computer.
        Accepts None if you do not want to set this value.

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('default_mpiprocs_per_machine', val)` property instead.

        """
        if def_cpus_per_machine is None:
            self.delete_property('default_mpiprocs_per_machine', raise_exception=False)
        else:
            if not isinstance(def_cpus_per_machine, int):
                raise TypeError('def_cpus_per_machine must be an integer (or None)')
        self.set_property('default_mpiprocs_per_machine', def_cpus_per_machine)

    def get_minimum_job_poll_interval(self):
        """
        Get the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('minimum_job_poll_interval')` instead.

        :return: The minimum interval (in seconds)
        :rtype: float
        """
        return self.get_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, 10)

    def set_minimum_job_poll_interval(self, interval):
        """
        Set the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('minimum_job_poll_interval', val)` property instead.

        :param interval: The minimum interval in seconds
        :type interval: float
        """
        self.set_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, interval)

    def get_workdir(self):
        """
        Get the working directory for this computer

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('work_dir')` instead.

        :return: The currently configured working directory
        :rtype: str
        """
        return self.get_property(self.PROPERTY_WORK_DIR, '/scratch/{username}/aiida_run/')

    def set_workdir(self, val):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('work_dir', val)` property instead.
        """
        self.set_property(self.PROPERTY_WORK_DIR, val)

    def get_shebang(self):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('shebang')` instead.
        """
        return self.get_property(self.PROPERTY_SHEBANG, '#!/bin/bash')

    def set_shebang(self, val):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('shebang', val)` property instead.

        :param str val: A valid shebang line
        """
        if not isinstance(val, str):
            raise ValueError('{} is invalid. Input has to be a string'.format(val))
        if not val.startswith('#!'):
            raise ValueError('{} is invalid. A shebang line has to start with #!'.format(val))
        metadata = self.get_metadata()
        metadata['shebang'] = val
        self.set_metadata(metadata)

    def get_prepend_text(self):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('prepend_text')` instead.
        """
        return self.get_property('prepend_text', '')

    def set_prepend_text(self, val):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('prepend_text', val)` property instead.
        """
        self.set_property('prepend_text', str(val))

    def get_append_text(self):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.get_property('append_text')` instead.
        """
        return self.get_property('append_text', '')

    def set_append_text(self, val):
        """
        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`: use `self.set_property('append_text', val)` property instead.
        """
        self.set_property('append_text', str(val))

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: get schema of the computer

        .. deprecated:: 1.0.0

            Will be removed in `v2.0.0`.
            Use :meth:`~aiida.restapi.translator.base.BaseTranslator.get_projectable_properties` instead.

        """
        message = 'method is deprecated, use' \
            '`aiida.restapi.translator.base.BaseTranslator.get_projectable_properties` instead'
        warnings.warn(message, AiidaDeprecationWarning)  # pylint: disable=no-member

        return {
            'description': {
                'display_name': 'Description',
                'help_text': 'short description of the Computer',
                'is_foreign_key': False,
                'type': 'str'
            },
            'hostname': {
                'display_name': 'Host',
                'help_text': 'Name of the host',
                'is_foreign_key': False,
                'type': 'str'
            },
            'id': {
                'display_name': 'Id',
                'help_text': 'Id of the object',
                'is_foreign_key': False,
                'type': 'int'
            },
            'name': {
                'display_name': 'Name',
                'help_text': 'Name of the object',
                'is_foreign_key': False,
                'type': 'str'
            },
            'scheduler_type': {
                'display_name': 'Scheduler',
                'help_text': 'Scheduler type',
                'is_foreign_key': False,
                'type': 'str',
                'valid_choices': {
                    'direct': {
                        'doc': 'Support for the direct execution bypassing schedulers.'
                    },
                    'pbsbaseclasses.PbsBaseClass': {
                        'doc': 'Base class with support for the PBSPro scheduler'
                    },
                    'pbspro': {
                        'doc': 'Subclass to support the PBSPro scheduler'
                    },
                    'sge': {
                        'doc':
                        'Support for the Sun Grid Engine scheduler and its variants/forks (Son of Grid Engine, '
                        'Oracle Grid Engine, ...)'
                    },
                    'slurm': {
                        'doc': 'Support for the SLURM scheduler (http://slurm.schedmd.com/).'
                    },
                    'torque': {
                        'doc': 'Subclass to support the Torque scheduler.'
                    }
                }
            },
            'transport_type': {
                'display_name': 'Transport type',
                'help_text': 'Transport Type',
                'is_foreign_key': False,
                'type': 'str',
                'valid_choices': {
                    'local': {
                        'doc':
                        'Support copy and command execution on the same host on which AiiDA is running via direct '
                        'file copy and execution commands.'
                    },
                    'ssh': {
                        'doc':
                        'Support connection, command execution and data transfer to remote computers via SSH+SFTP.'
                    }
                }
            },
            'uuid': {
                'display_name': 'Unique ID',
                'help_text': 'Universally Unique Identifier',
                'is_foreign_key': False,
                'type': 'unicode'
            }
        }

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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import logging
import os
import warnings
import six

from aiida import transports, schedulers
from aiida.common import exceptions
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.manage.manager import get_manager
from aiida.plugins import SchedulerFactory, TransportFactory

from . import entities
from . import users

__all__ = ('Computer',)


class Computer(entities.Entity):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything only on store().
    After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) metadata can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in the 'type' field.
    """
    # pylint: disable=too-many-public-methods

    _logger = logging.getLogger(__name__)

    PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL = 'minimum_scheduler_poll_interval'  # pylint: disable=invalid-name
    PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT = 10.  # pylint: disable=invalid-name
    PROPERTY_WORKDIR = 'workdir'
    PROPERTY_SHEBANG = 'shebang'

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
        """Construct a new computer

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
        super(Computer, self).__init__(model)
        if workdir is not None:
            self.set_workdir(workdir)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return '{} ({}), pk: {}'.format(self.name, self.hostname, self.pk)

    @property
    def full_text_info(self):
        """
        Return a (multiline) string with a human-readable detailed information on this computer.

        :rtype: str
        """
        ret_lines = []
        ret_lines.append('Computer name:     {}'.format(self.name))
        ret_lines.append(' * PK:             {}'.format(self.pk))
        ret_lines.append(' * UUID:           {}'.format(self.uuid))
        ret_lines.append(' * Description:    {}'.format(self.description))
        ret_lines.append(' * Hostname:       {}'.format(self.hostname))
        ret_lines.append(' * Transport type: {}'.format(self.get_transport_type()))
        ret_lines.append(' * Scheduler type: {}'.format(self.get_scheduler_type()))
        ret_lines.append(' * Work directory: {}'.format(self.get_workdir()))
        ret_lines.append(' * Shebang:        {}'.format(self.get_shebang()))
        ret_lines.append(' * mpirun command: {}'.format(' '.join(self.get_mpirun_command())))
        def_cpus_machine = self.get_default_mpiprocs_per_machine()
        if def_cpus_machine is not None:
            ret_lines.append(' * Default number of cpus per machine: {}'.format(def_cpus_machine))
        # pylint: disable=fixme
        # TODO: Put back following line when we port Node to new backend system
        # ret_lines.append(" * Used by:        {} nodes".format(len(self._dbcomputer.dbnodes.all())))

        ret_lines.append(' * prepend text:')
        if self.get_prepend_text().strip():
            for line in self.get_prepend_text().split('\n'):
                ret_lines.append('   {}'.format(line))
        else:
            ret_lines.append('   # No prepend text.')
        ret_lines.append(' * append text:')
        if self.get_append_text().strip():
            for line in self.get_append_text().split('\n'):
                ret_lines.append('   {}'.format(line))
        else:
            ret_lines.append('   # No append text.')

        return '\n'.join(ret_lines)

    @property
    def logger(self):
        return self._logger

    # region validation

    @classmethod
    def _name_validator(cls, name):
        """
        Validates the name.
        """
        if not name.strip():
            raise exceptions.ValidationError('No name specified')

    @classmethod
    def _hostname_validator(cls, hostname):
        """
        Validates the hostname.
        """
        if not hostname.strip():
            raise exceptions.ValidationError('No hostname specified')

    @classmethod
    def _description_validator(cls, description):
        """
        Validates the description.
        """
        # The description is always valid

    @classmethod
    def _transport_type_validator(cls, transport_type):
        """
        Validates the transport string.
        """
        if transport_type not in transports.Transport.get_valid_transports():
            raise exceptions.ValidationError('The specified transport is not a valid one')

    @classmethod
    def _scheduler_type_validator(cls, scheduler_type):
        """
        Validates the transport string.
        """
        if scheduler_type not in schedulers.Scheduler.get_valid_schedulers():
            raise exceptions.ValidationError('The specified scheduler is not a valid one')

    @classmethod
    def _prepend_text_validator(cls, prepend_text):
        """
        Validates the prepend text string.
        """
        # no validation done

    @classmethod
    def _append_text_validator(cls, append_text):
        """
        Validates the append text string.
        """
        # no validation done

    @classmethod
    def _workdir_validator(cls, workdir):
        """
        Validates the transport string.
        """
        if not workdir.strip():
            raise exceptions.ValidationError('No workdir specified')

        try:
            convertedwd = workdir.format(username='test')
        except KeyError as exc:
            raise exceptions.ValidationError('In workdir there is an unknown replacement field {}'.format(exc.args[0]))
        except ValueError as exc:
            raise exceptions.ValidationError("Error in the string: '{}'".format(exc))

        if not os.path.isabs(convertedwd):
            raise exceptions.ValidationError('The workdir must be an absolute path')

    def _mpirun_command_validator(self, mpirun_cmd):
        """
        Validates the mpirun_command variable. MUST be called after properly
        checking for a valid scheduler.
        """
        if not isinstance(mpirun_cmd, (tuple, list)) or not all(isinstance(i, six.string_types) for i in mpirun_cmd):
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
            raise exceptions.ValidationError('In workdir there is an unknown replacement field {}'.format(exc.args[0]))
        except ValueError as exc:
            raise exceptions.ValidationError("Error in the string: '{}'".format(exc))

    def validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr and similar methods
        that automatically read either from the DB or from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super().validate() method first!
        """
        if not self.get_name().strip():
            raise exceptions.ValidationError('No name specified')

        self._hostname_validator(self.get_hostname())
        self._description_validator(self.get_description())
        self._transport_type_validator(self.get_transport_type())
        self._scheduler_type_validator(self.get_scheduler_type())
        self._workdir_validator(self.get_workdir())

        try:
            mpirun_cmd = self.get_mpirun_command()
        except exceptions.DbContentError:
            raise exceptions.ValidationError('Error in the DB content of the metadata')

        # To be called AFTER the validation of the scheduler
        self._mpirun_command_validator(mpirun_cmd)

    @classmethod
    def _default_mpiprocs_per_machine_validator(cls, def_cpus_per_machine):
        """
        Validates the default number of CPUs per machine (node)
        """
        if def_cpus_per_machine is None:
            return

        if not isinstance(def_cpus_per_machine, six.integer_types) or def_cpus_per_machine <= 0:
            raise exceptions.ValidationError(
                'Invalid value for default_mpiprocs_per_machine, '
                'must be a positive integer, or an empty '
                'string if you do not want to provide a '
                'default value.'
            )

    # endregion

    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.
        """
        return Computer.from_backend_entity(self._backend_entity.copy())

    def store(self):
        """
        Store the computer in the DB.

        Differently from Nodes, a computer can be re-stored if its properties
        are to be changed (e.g. a new mpirun command, etc.)
        """
        self.validate()
        return super(Computer, self).store()

    @property
    def name(self):
        return self._backend_entity.name

    @property
    def label(self):
        """
        The computer label
        """
        return self.name

    @label.setter
    def label(self, value):
        """
        Set the computer label (i.e., name)
        """
        self.set_name(value)

    @property
    def description(self):
        """
        Get a description of the computer

        :return: the description
        :rtype: str
        """
        return self._backend_entity.description

    @property
    def hostname(self):
        return self._backend_entity.hostname

    def get_metadata(self):
        return self._backend_entity.get_metadata()

    def set_metadata(self, metadata):
        """
        Set the metadata.

        .. note: You still need to call the .store() method to actually save
           data to the database! (The store method can be called multiple
           times, differently from AiiDA Node objects).
        """
        self._backend_entity.set_metadata(metadata)

    def delete_property(self, name, raise_exception=True):
        """
        Delete a property from this computer

        :param name: the name of the property
        :type name: str

        :param raise_exception: if True raise if the property does not exist, otherwise return None
        :type raise_exception: bool
        """
        olddata = self.get_metadata()
        try:
            del olddata[name]
            self.set_metadata(olddata)
        except KeyError:
            if raise_exception:
                raise AttributeError("'{}' property not found".format(name))

    def set_property(self, name, value):
        """
        Set a property on this computer

        :param name: the property name
        :param value: the new value
        """
        metadata = self.get_metadata() or {}
        metadata[name] = value
        self.set_metadata(metadata)

    def get_property(self, name, *args):
        """
        Get a property of this computer

        :param name: the property name
        :type name: str

        :param args: additional arguments

        :return: the property value
        """
        if len(args) > 1:
            raise TypeError('get_property expected at most 2 arguments')
        olddata = self.get_metadata()
        try:
            return olddata[name]
        except KeyError:
            if not args:
                raise AttributeError("'{}' property not found".format(name))
            return args[0]

    def get_prepend_text(self):
        return self.get_property('prepend_text', '')

    def set_prepend_text(self, val):
        self.set_property('prepend_text', six.text_type(val))

    def get_append_text(self):
        return self.get_property('append_text', '')

    def set_append_text(self, val):
        self.set_property('append_text', six.text_type(val))

    def get_mpirun_command(self):
        """
        Return the mpirun command. Must be a list of strings, that will be
        then joined with spaces when submitting.

        I also provide a sensible default that may be ok in many cases.
        """
        return self.get_property('mpirun_command', ['mpirun', '-np', '{tot_num_mpiprocs}'])

    def set_mpirun_command(self, val):
        """
        Set the mpirun command. It must be a list of strings (you can use
        string.split() if you have a single, space-separated string).
        """
        if not isinstance(val, (tuple, list)) or not all(isinstance(i, six.string_types) for i in val):
            raise TypeError('the mpirun_command must be a list of strings')
        self.set_property('mpirun_command', val)

    def get_default_mpiprocs_per_machine(self):
        """
        Return the default number of CPUs per machine (node) for this computer,
        or None if it was not set.
        """
        return self.get_property('default_mpiprocs_per_machine', None)

    def set_default_mpiprocs_per_machine(self, def_cpus_per_machine):
        """
        Set the default number of CPUs per machine (node) for this computer.
        Accepts None if you do not want to set this value.
        """
        if def_cpus_per_machine is None:
            self.delete_property('default_mpiprocs_per_machine', raise_exception=False)
        else:
            if not isinstance(def_cpus_per_machine, six.integer_types):
                raise TypeError('def_cpus_per_machine must be an integer (or None)')
        self.set_property('default_mpiprocs_per_machine', def_cpus_per_machine)

    def get_minimum_job_poll_interval(self):
        """
        Get the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        :return: The minimum interval (in seconds)
        :rtype: float
        """
        return self.get_property(
            self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT
        )

    def set_minimum_job_poll_interval(self, interval):
        """
        Set the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        :param interval: The minimum interval in seconds
        :type interval: float
        """
        self.set_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, interval)

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

    def get_workdir(self):
        """
        Get the working directory for this computer
        :return: The currently configured working directory
        :rtype: str
        """
        return self.get_property(self.PROPERTY_WORKDIR, '/scratch/{username}/aiida_run/')

    def set_workdir(self, val):
        self.set_property(self.PROPERTY_WORKDIR, val)

    def get_shebang(self):
        return self.get_property(self.PROPERTY_SHEBANG, '#!/bin/bash')

    def set_shebang(self, val):
        """
        :param str val: A valid shebang line
        """
        if not isinstance(val, six.string_types):
            raise ValueError('{} is invalid. Input has to be a string'.format(val))
        if not val.startswith('#!'):
            raise ValueError('{} is invalid. A shebang line has to start with #!'.format(val))
        metadata = self.get_metadata()
        metadata['shebang'] = val
        self.set_metadata(metadata)

    def get_name(self):
        return self._backend_entity.get_name()

    def set_name(self, val):
        self._backend_entity.set_name(val)

    def get_hostname(self):
        """
        Get this computer hostname
        :rtype: str
        """
        return self._backend_entity.get_hostname()

    def set_hostname(self, val):
        """
        Set the hostname of this computer
        :param val: The new hostname
        :type val: str
        """
        self._backend_entity.set_hostname(val)

    def get_description(self):
        """
        Get the description for this computer

        :return: the description
        :rtype: str
        """

    def set_description(self, val):
        """
        Set the description for this computer

        :param val: the new description
        :type val: str
        """
        self._backend_entity.set_description(val)

    def get_authinfo(self, user):
        """
        Return the aiida.orm.authinfo.AuthInfo instance for the
        given user on this computer, if the computer
        is configured for the given user.

        :param user: a User instance.
        :return: a AuthInfo instance
        :raise aiida.common.NotExistent: if the computer is not configured for the given
            user.
        """
        from . import authinfos

        return authinfos.AuthInfo.objects(self.backend).get(dbcomputer_id=self.id, aiidauser_id=user.id)

    def is_user_configured(self, user):
        """
        Is the user configured on this computer?

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
        """
        Is the given user enabled to run on this computer?

        :param user: the user to check
        :return: True if enabled, False otherwise
        :rtype: bool
        """
        try:
            authinfo = self.get_authinfo(user)
            return authinfo.enabled
        except exceptions.NotExistent:
            # Return False if the user is not configured (in a sense,
            # it is disabled for that user)
            return False

    def get_scheduler_type(self):
        """
        Get the scheduler type for this computer

        :return: the scheduler type
        :rtype: str
        """
        return self._backend_entity.get_scheduler_type()

    def set_scheduler_type(self, scheduler_type):
        """
        :param scheduler_type: the new scheduler type
        """
        self._scheduler_type_validator(scheduler_type)
        self._backend_entity.set_scheduler_type(scheduler_type)

    def get_transport_type(self):
        """
        Get the current transport type for this computer

        :return: the transport type
        :rtype: str
        """
        return self._backend_entity.get_transport_type()

    def set_transport_type(self, transport_type):
        """
        Set the transport type for this computer

        :param transport_type: the new transport type
        :type transport_type: str
        """
        self._backend_entity.set_transport_type(transport_type)

    def get_transport_class(self):
        """
        Get the transport class for this computer.  Can be used to instantiate a transport instance.

        :return: the transport class
        """
        try:
            return TransportFactory(self.get_transport_type())
        except exceptions.EntryPointError as exception:
            raise exceptions.ConfigurationError(
                'No transport found for {} [type {}], message: {}'.format(
                    self.name, self.get_transport_type(), exception
                )
            )

    def get_scheduler(self):
        """
        Get a scheduler instance for this computer

        :return: the scheduler instance
        :rtype: :class:`aiida.schedulers.Scheduler`
        """
        try:
            scheduler_class = SchedulerFactory(self.get_scheduler_type())
            # I call the init without any parameter
            return scheduler_class()
        except exceptions.EntryPointError as exception:
            raise exceptions.ConfigurationError(
                'No scheduler found for {} [type {}], message: {}'.format(
                    self.name, self.get_scheduler_type(), exception
                )
            )

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

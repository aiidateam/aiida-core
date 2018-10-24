# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The computer backend abstract classes"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import logging
import os
import six

from aiida import transport, scheduler
from aiida.common import exceptions
from .backend import Collection, CollectionEntry

__all__ = ['Computer', 'ComputerCollection']


@six.add_metaclass(abc.ABCMeta)
class ComputerCollection(Collection):
    """The collection of Computer entries."""

    @abc.abstractmethod
    def create(self,
               name,
               hostname,
               description='',
               transport_type='',
               scheduler_type='',
               workdir=None,
               enabled_state=True):
        # pylint: disable=too-many-arguments
        """
        Create new a computer

        :return: the newly created computer
        :rtype: :class:`aiida.orm.Computer`
        """
        pass

    def get(self, id=None, name=None, uuid=None):  # pylint: disable=redefined-builtin, invalid-name
        """
        Get a computer from one of it's unique identifiers

        :param id: the computer's id
        :param name: the name of the computer
        :type name: str
        :param uuid: the uuid of the computer
        :return: the corresponding computer
        :rtype: :class:`aiida.orm.Computer`
        """
        query = self.backend.query_builder()
        filters = {}
        if id is not None:
            filters['id'] = {'==': id}
        if name is not None:
            filters['name'] = {'==': name}
        if uuid is not None:
            filters['uuid'] = {'==': uuid}

        query.append(Computer, filters=filters)
        res = [_[0] for _ in query.all()]
        if not res:
            raise exceptions.NotExistent("No computer with filter '{}' found".format(filters))
        if len(res) > 1:
            raise exceptions.MultipleObjectsError("Multiple computers found with the same id '{}'".format(id))

        return res[0]

    @abc.abstractmethod
    def list_names(self):
        """
        Return a list with all the names of the computers in the DB.
        """
        pass

    @abc.abstractmethod
    def delete(self, id):  # pylint: disable=invalid-name, redefined-builtin
        """ Delete the computer with the given id """
        pass


@six.add_metaclass(abc.ABCMeta)
class Computer(CollectionEntry):
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

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: get schema of the computer
        """
        return {
            "description": {
                "display_name": "Description",
                "help_text": "short description of the Computer",
                "is_foreign_key": False,
                "type": "str"
            },
            "enabled": {
                "display_name": "Enabled",
                "help_text": "True(False) if the computer is(not) enabled to run jobs",
                "is_foreign_key": False,
                "type": "bool"
            },
            "hostname": {
                "display_name": "Host",
                "help_text": "Name of the host",
                "is_foreign_key": False,
                "type": "str"
            },
            "id": {
                "display_name": "Id",
                "help_text": "Id of the object",
                "is_foreign_key": False,
                "type": "int"
            },
            "name": {
                "display_name": "Name",
                "help_text": "Name of the object",
                "is_foreign_key": False,
                "type": "str"
            },
            "scheduler_type": {
                "display_name": "Scheduler",
                "help_text": "Scheduler type",
                "is_foreign_key": False,
                "type": "str",
                "valid_choices": {
                    "direct": {
                        "doc": "Support for the direct execution bypassing schedulers."
                    },
                    "pbsbaseclasses.PbsBaseClass": {
                        "doc": "Base class with support for the PBSPro scheduler"
                    },
                    "pbspro": {
                        "doc": "Subclass to support the PBSPro scheduler"
                    },
                    "sge": {
                        "doc":
                        "Support for the Sun Grid Engine scheduler and its variants/forks (Son of Grid Engine, "
                        "Oracle Grid Engine, ...)"
                    },
                    "slurm": {
                        "doc": "Support for the SLURM scheduler (http://slurm.schedmd.com/)."
                    },
                    "torque": {
                        "doc": "Subclass to support the Torque scheduler.."
                    }
                }
            },
            "transport_params": {
                "display_name": "",
                "help_text": "Transport Parameters",
                "is_foreign_key": False,
                "type": "str"
            },
            "transport_type": {
                "display_name": "Transport type",
                "help_text": "Transport Type",
                "is_foreign_key": False,
                "type": "str",
                "valid_choices": {
                    "local": {
                        "doc":
                        "Support copy and command execution on the same host on which AiiDA is running via direct file "
                        "copy and execution commands."
                    },
                    "ssh": {
                        "doc":
                        "Support connection, command execution and data transfer to remote computers via SSH+SFTP."
                    }
                }
            },
            "uuid": {
                "display_name": "Unique ID",
                "help_text": "Universally Unique Identifier",
                "is_foreign_key": False,
                "type": "unicode"
            }
        }

    def pk(self):
        """
        Return the principal key in the DB.
        """
        return self.id

    @abc.abstractproperty
    def uuid(self):
        """
        Return the UUID in the DB.
        """
        pass

    @abc.abstractproperty
    def id(self):  # pylint: disable=invalid-name
        """
        Return the ID in the DB.
        """
        pass

    @abc.abstractmethod
    def set(self, **kwargs):
        pass

    @abc.abstractproperty
    def full_text_info(self):
        """
        Return a (multiline) string with a human-readable detailed information on this computer.

        :rypte: str
        """
        pass

    @abc.abstractproperty
    def is_stored(self):
        """
        Is the computer stored?

        :return: True if stored, False otherwise
        :rtype: bool
        """

    @property
    def logger(self):
        return self._logger

    @classmethod
    def _name_validator(cls, name):
        """
        Validates the name.
        """
        if not name.strip():
            raise exceptions.ValidationError("No name specified")

    @classmethod
    def _hostname_validator(cls, hostname):
        """
        Validates the hostname.
        """
        if not hostname.strip():
            raise exceptions.ValidationError("No hostname specified")

    @classmethod
    def _enabled_state_validator(cls, enabled_state):
        """
        Validates the hostname.
        """
        if not isinstance(enabled_state, bool):
            raise exceptions.ValidationError("Invalid value '{}' for the enabled state, must "
                                             "be a boolean".format(str(enabled_state)))

    @classmethod
    def _description_validator(cls, description):
        """
        Validates the description.
        """
        # The description is always valid
        pass

    @classmethod
    def _transport_type_validator(cls, transport_type):
        """
        Validates the transport string.
        """
        if transport_type not in transport.Transport.get_valid_transports():
            raise exceptions.ValidationError("The specified transport is not a valid one")

    @classmethod
    def _scheduler_type_validator(cls, scheduler_type):
        """
        Validates the transport string.
        """
        if scheduler_type not in scheduler.Scheduler.get_valid_schedulers():
            raise exceptions.ValidationError("The specified scheduler is not a valid one")

    @classmethod
    def _prepend_text_validator(cls, prepend_text):
        """
        Validates the prepend text string.
        """
        # no validation done
        pass

    @classmethod
    def _append_text_validator(cls, append_text):
        """
        Validates the append text string.
        """
        # no validation done
        pass

    @classmethod
    def _workdir_validator(cls, workdir):
        """
        Validates the transport string.
        """
        if not workdir.strip():
            raise exceptions.ValidationError("No workdir specified")

        try:
            convertedwd = workdir.format(username="test")
        except KeyError as exc:
            raise exceptions.ValidationError("In workdir there is an unknown replacement field {}".format(exc.args[0]))
        except ValueError as exc:
            raise exceptions.ValidationError("Error in the string: '{}'".format(exc))

        if not os.path.isabs(convertedwd):
            raise exceptions.ValidationError("The workdir must be an absolute path")

    def _mpirun_command_validator(self, mpirun_cmd):
        """
        Validates the mpirun_command variable. MUST be called after properly
        checking for a valid scheduler.
        """
        if not isinstance(mpirun_cmd, (tuple, list)) or not all(isinstance(i, six.string_types) for i in mpirun_cmd):
            raise exceptions.ValidationError("the mpirun_command must be a list of strings")

        try:
            job_resource_keys = self.get_scheduler().job_resource_class.get_valid_keys()
        except exceptions.MissingPluginError:
            raise exceptions.ValidationError("Unable to load the scheduler for this computer")

        subst = {i: 'value' for i in job_resource_keys}
        subst['tot_num_mpiprocs'] = 'value'

        try:
            for arg in mpirun_cmd:
                arg.format(**subst)
        except KeyError as exc:
            raise exceptions.ValidationError("In workdir there is an unknown replacement field {}".format(exc.args[0]))
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
            raise exceptions.ValidationError("No name specified")

        self._hostname_validator(self.get_hostname())
        self._description_validator(self.get_description())
        self._enabled_state_validator(self.is_enabled())
        self._transport_type_validator(self.get_transport_type())
        self._scheduler_type_validator(self.get_scheduler_type())
        self._workdir_validator(self.get_workdir())

        try:
            mpirun_cmd = self.get_mpirun_command()
        except exceptions.DbContentError:
            raise exceptions.ValidationError("Error in the DB content of the transport_params")

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
            raise exceptions.ValidationError("Invalid value for default_mpiprocs_per_machine, "
                                             "must be a positive integer, or an empty "
                                             "string if you do not want to provide a "
                                             "default value.")

    @abc.abstractmethod
    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.
        """
        pass

    @abc.abstractmethod
    def store(self):
        """
        Store the computer in the DB.

        Differently from Nodes, a computer can be re-stored if its properties
        are to be changed (e.g. a new mpirun command, etc.)
        """
        pass

    @abc.abstractproperty
    def name(self):
        pass

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

    @abc.abstractproperty
    def description(self):
        pass

    @abc.abstractproperty
    def hostname(self):
        pass

    @abc.abstractmethod
    def _get_metadata(self):
        pass

    @abc.abstractmethod
    def _set_metadata(self, metadata_dict):
        """
        Set the metadata.

        .. note: You still need to call the .store() method to actually save
           data to the database! (The store method can be called multiple
           times, differently from AiiDA Node objects).
        """
        pass

    def _del_property(self, name, raise_exception=True):
        """
        Delete a property from this computer

        :param name: the name of the property
        :param raise_exception: if True raise if the property does not exist, otherwise return None
        """
        olddata = self._get_metadata()
        try:
            del olddata[name]
        except KeyError:
            if raise_exception:
                raise AttributeError("'{}' property not found".format(name))
            else:
                # Do not reset the metadata, it is not necessary
                return
        self._set_metadata(olddata)

    def _set_property(self, name, value):
        """
        Set a property on this computer

        :param name: the property name
        :param value: the new value
        """
        olddata = self._get_metadata()
        olddata[name] = value
        self._set_metadata(olddata)

    def _get_property(self, name, *args):
        """
        Get a property of this computer

        :param name: the property name
        :param args: additional arguments
        :return: the property value
        """
        if len(args) > 1:
            raise TypeError("_get_property expected at most 2 arguments")
        olddata = self._get_metadata()
        try:
            return olddata[name]
        except KeyError:
            if not args:
                raise AttributeError("'{}' property not found".format(name))
            elif len(args) == 1:
                return args[0]

    def get_prepend_text(self):
        return self._get_property("prepend_text", "")

    def set_prepend_text(self, val):
        self._set_property("prepend_text", six.text_type(val))

    def get_append_text(self):
        return self._get_property("append_text", "")

    def set_append_text(self, val):
        self._set_property("append_text", six.text_type(val))

    def get_mpirun_command(self):
        """
        Return the mpirun command. Must be a list of strings, that will be
        then joined with spaces when submitting.

        I also provide a sensible default that may be ok in many cases.
        """
        return self._get_property("mpirun_command", ["mpirun", "-np", "{tot_num_mpiprocs}"])

    def set_mpirun_command(self, val):
        """
        Set the mpirun command. It must be a list of strings (you can use
        string.split() if you have a single, space-separated string).
        """
        if not isinstance(val, (tuple, list)) or not all(isinstance(i, six.string_types) for i in val):
            raise TypeError("the mpirun_command must be a list of strings")
        self._set_property("mpirun_command", val)

    def get_default_mpiprocs_per_machine(self):
        """
        Return the default number of CPUs per machine (node) for this computer,
        or None if it was not set.
        """
        return self._get_property("default_mpiprocs_per_machine", None)

    def set_default_mpiprocs_per_machine(self, def_cpus_per_machine):
        """
        Set the default number of CPUs per machine (node) for this computer.
        Accepts None if you do not want to set this value.
        """
        if def_cpus_per_machine is None:
            self._del_property("default_mpiprocs_per_machine", raise_exception=False)
        else:
            if not isinstance(def_cpus_per_machine, six.integer_types):
                raise TypeError("def_cpus_per_machine must be an integer (or None)")
        self._set_property("default_mpiprocs_per_machine", def_cpus_per_machine)

    def get_minimum_job_poll_interval(self):
        """
        Get the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        :return: The minimum interval (in seconds)
        :rtype: float
        """
        return self._get_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL,
                                  self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL__DEFAULT)

    def set_minimum_job_poll_interval(self, interval):
        """
        Set the minimum interval between subsequent requests to update the list
        of jobs currently running on this computer.

        :param interval: The minimum interval in seconds
        :type interval: float
        """
        self._set_property(self.PROPERTY_MINIMUM_SCHEDULER_POLL_INTERVAL, interval)

    @abc.abstractmethod
    def get_transport_params(self):
        pass

    @abc.abstractmethod
    def set_transport_params(self, val):
        pass

    def get_transport(self, user=None):
        """
        Return a Tranport class, configured with all correct parameters.
        The Transport is closed (meaning that if you want to run any operation with
        it, you have to open it first (i.e., e.g. for a SSH tranport, you have
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
        from aiida.orm.backend import construct_backend
        backend = construct_backend()
        if user is None:
            authinfo = backend.authinfos.get(self, backend.users.get_automatic_user())
        else:
            authinfo = backend.authinfos.get(self, user)

        return authinfo.get_transport()

    @abc.abstractmethod
    def get_workdir(self):
        """
        Get the working directory for this computer
        :return: The currently configured working directory
        :rtype: str
        """
        pass

    @abc.abstractmethod
    def get_shebang(self):
        pass

    @abc.abstractmethod
    def set_workdir(self, val):
        pass

    def set_shebang(self, val):
        """
        :param str val: A valid shebang line
        """
        if not isinstance(val, six.string_types):
            raise ValueError("{} is invalid. Input has to be a string".format(val))
        if not val.startswith('#!'):
            raise ValueError("{} is invalid. A shebang line has to start with #!".format(val))
        metadata = self._get_metadata()
        metadata['shebang'] = val
        self._set_metadata(metadata)

    @abc.abstractmethod
    def get_name(self):
        pass

    @abc.abstractmethod
    def set_name(self, val):
        pass

    def get_hostname(self):
        """
        Get this computer hostname
        :rtype: str
        """
        pass

    @abc.abstractmethod
    def set_hostname(self, val):
        """
        Set the hostname of this computer
        :param val: The new hostname
        :type val: str
        """
        pass

    @abc.abstractmethod
    def get_description(self):
        """
        Get the description for this computer

        :return: the description
        :rtype: str
        """
        pass

    @abc.abstractmethod
    def set_description(self, val):
        """
        Set the description for this computer

        :param val: the new description
        :type val: str
        """
        pass

    @abc.abstractmethod
    def get_calculations_on_computer(self):
        """
        Get the calculations corresponding to this computer

        :return: a list of calculations on this computer
        """
        pass

    @abc.abstractmethod
    def is_enabled(self):
        """
        Is the computer enabled

        :return: True if enabled, False otherwise
        :rtype: bool
        """
        pass

    def get_authinfo(self, user):
        """
        Return the aiida.orm.authinfo.AuthInfo instance for the
        given user on this computer, if the computer
        is configured for the given user.

        :param user: a User instance.
        :return: a AuthInfo instance
        :raise NotExistent: if the computer is not configured for the given
            user.
        """
        return self.backend.authinfos.get(computer=self, user=user)

    def is_user_configured(self, user):
        """
        Check if the user is configured on this computer

        :param user: the user to check
        :return: True if enabled, False otherwise
        """
        try:
            self.get_authinfo(user)
            return True
        except exceptions.NotExistent:
            return False

    def is_user_enabled(self, user):
        """
        Check if a user is enabled to run on this computer

        :param user: the user to check
        :return: True if enabled, False otherwise
        """
        try:
            authinfo = self.get_authinfo(user)
            return authinfo.enabled
        except exceptions.NotExistent:
            # Return False if the user is not configured (in a sense,
            # it is disabled for that user)
            return False

    @abc.abstractmethod
    def set_enabled_state(self, enabled):
        """
        Set the enable state for this computer

        :param enabled: True if enabled, False otherwise
        """

    @abc.abstractmethod
    def get_scheduler_type(self):
        """
        Get the scheduler type for this computer

        :return: the scheduler ype
        :rtype: str
        """
        pass

    @abc.abstractmethod
    def set_scheduler_type(self, val):
        """
        Set the scheduler type for this computer

        :param val: the new scheduler type
        :type val: str
        """
        pass

    @abc.abstractmethod
    def get_transport_type(self):
        """
        Get the transport type for this computer

        :return: the transport type
        :rtype: str
        """

    @abc.abstractmethod
    def set_transport_type(self, val):
        """
        Set the transport type for this computer

        :param val: the new transport type
        :type val: str
        """
        pass

    def get_transport_class(self):
        """
        Get the transport class for this computer.  Can be used to instantiate a transport instance.

        :return: the transport class
        """
        try:
            # I return the class, not an instance
            return transport.TransportFactory(self.get_transport_type())
        except exceptions.MissingPluginError as exc:
            raise exceptions.ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.name, self.get_transport_type(), exc))

    def get_scheduler(self):
        """
        Get the scheduler instance for this computer

        :return: the scheduler
        """
        try:
            scheduler_class = scheduler.SchedulerFactory(self.get_scheduler_type())
            # I call the init without any parameter
            return scheduler_class()
        except exceptions.MissingPluginError as exc:
            raise exceptions.ConfigurationError('No scheduler found for {} [type {}], message: {}'.format(
                self.name, self.get_scheduler_type(), exc))

    def configure(self, user=None, **kwargs):
        """
        Configure a computer for a user with valid auth params passed via kwargs

        :param user: the user to configure the computer for
        :kwargs: the configuration keywords with corresponding values
        :return: the authinfo object for the configured user
        :rtype: :class:`aiida.orm.AuthInfo`
        """

        transport_cls = self.get_transport_class()
        backend = self.backend
        user = user or backend.users.get_automatic_user()

        try:
            authinfo = self.get_authinfo(user)
        except exceptions.NotExistent:
            authinfo = backend.authinfos.create(self, user)

        auth_params = authinfo.get_auth_params()
        valid_keys = set(transport_cls.get_valid_auth_params())

        if not set(kwargs.keys()).issubset(valid_keys):
            invalid_keys = [key for key in kwargs if key not in valid_keys]
            raise ValueError('{transport}: recieved invalid authentication parameter(s) "{invalid}"'.format(
                transport=transport_cls, invalid=invalid_keys))

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
        user = user or backend.users.get_automatic_user()

        config = {}
        try:
            authinfo = backend.authinfos.get(self, user)
            config = authinfo.get_auth_params()
        except exceptions.NotExistent:
            pass

        return config

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self.is_enabled():
            return "{} ({}), pk: {}".format(self.name, self.hostname, self.pk)

        return "{} ({}) [DISABLED], pk: {}".format(self.name, self.hostname, self.pk)

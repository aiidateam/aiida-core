# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin represeting a containter executable code to be wrapped and called through a `CalcJob` plugin."""
import os

from aiida.common import exceptions
from aiida.common.log import override_log_level

from .data import Data

__all__ = ('ContainerCode',)


class ContainerCode(Data):
    """
    A container code entity.
    """

    # pylint: disable=too-many-public-methods

    def __init__(self, computer=None, container_thing=None, image=None, container_exec_path=None, input_plugin_name=None, **kwargs):
        super().__init__(**kwargs)

        # do some check of parameters

        self.set_container_exec(computer, container_thing, image, container_exec_path)

        if input_plugin_name:
            self.set_input_plugin_name(input_plugin_name)

    HIDDEN_KEY = 'hidden'

    def hide(self):
        """
        Hide the code (prevents from showing it in the verdi code list)
        """
        self.set_extra(self.HIDDEN_KEY, True)

    def reveal(self):
        """
        Reveal the code (allows to show it in the verdi code list)
        By default, it is revealed
        """
        self.set_extra(self.HIDDEN_KEY, False)

    @property
    def hidden(self):
        """
        Determines whether the Code is hidden or not
        """
        return self.get_extra(self.HIDDEN_KEY, False)

    def __str__(self):
        computer_str = self.computer.label
        container_str = 'Sarus' # TODO get from container input inputs of instance
        return f"Container code '{self.label}' on {computer_str} with container technology {container_str}, pk: {self.pk}, uuid: {self.uuid}"

    def get_computer_label(self):
        """Get label of this code's computer."""
        return self.computer.label

    @property
    def full_label(self):
        """Get full label of this code.

        Returns label of the form <code-label>@<computer-name>.
        """
        return f'{self.label}@{self.get_computer_label()}'

    @property
    def label(self):
        """Return the node label.

        :return: the label
        """
        super().label 

    @label.setter
    def label(self, value):
        """Set the label.

        :param value: the new value to set
        """
        if '@' in str(value):
            msg = "Code labels must not contain the '@' symbol"
            raise ValueError(msg)

        super(ContainerCode, self.__class__).label.fset(self, value)  # pylint: disable=no-member

    def relabel(self, new_label):
        """Relabel this code.

        :param new_label: new code label
        """
        # pylint: disable=unused-argument
        suffix = f'@{self.computer.label}'
        if new_label.endswith(suffix):
            new_label = new_label[:-len(suffix)]

        self.label = new_label

    def get_description(self):
        """Return a string description of this Code instance.

        :return: string description of this Code instance
        """
        return f'{self.description}'

    @classmethod
    def get_code_helper(cls, label, machinename=None, backend=None):
        """
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely
            a code
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.computers import Computer
        from aiida.orm.querybuilder import QueryBuilder

        query = QueryBuilder(backend=backend)
        query.append(cls, filters={'label': label}, project='*', tag='code')
        if machinename:
            query.append(Computer, filters={'label': machinename}, with_node='code')

        if query.count() == 0:
            raise NotExistent(f"'{label}' is not a valid code label.")
        elif query.count() > 1:
            codes = query.all(flat=True)
            retstr = f"There are multiple codes with label '{label}', having IDs: "
            retstr += f"{', '.join(sorted([str(c.pk) for c in codes]))}.\n"
            retstr += ('Relabel them (using their ID), or refer to them with their ID.')
            raise MultipleObjectsError(retstr)
        else:
            return query.first()[0]

    @classmethod
    def get(cls, pk=None, label=None, machinename=None):
        """
        Get a Computer object with given identifier string, that can either be
        the numeric ID (pk), or the label (and computername) (if unique).

        :param pk: the numeric ID (pk) for code
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely a code
        :raise ValueError: if neither a pk nor a label was passed in
        """
        # pylint: disable=arguments-differ
        from aiida.orm.utils import load_code

        # first check if code pk is provided
        if pk:
            code_int = int(pk)
            try:
                return load_code(pk=code_int)
            except exceptions.NotExistent:
                raise ValueError(f'{pk} is not valid code pk')
            except exceptions.MultipleObjectsError:
                raise exceptions.MultipleObjectsError(f"More than one code in the DB with pk='{pk}'!")

        # check if label (and machinename) is provided
        elif label is not None:
            return cls.get_code_helper(label, machinename)

        else:
            raise ValueError('Pass either pk or code label (and machinename)')

    @classmethod
    def get_from_string(cls, code_string):
        """
        Get a Computer object with given identifier string in the format
        label@machinename. See the note below for details on the string
        detection algorithm.

        .. note:: the (leftmost) '@' symbol is always used to split code
            and computername. Therefore do not use
            '@' in the code name if you want to use this function
            ('@' in the computer name are instead valid).

        :param code_string: the code string identifying the code to load

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely
            a code
        :raise TypeError: if code_string is not of string type

        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent

        try:
            label, _, machinename = code_string.partition('@')
        except AttributeError:
            raise TypeError('the provided code_string is not of valid string type')

        try:
            return cls.get_code_helper(label, machinename)
        except NotExistent:
            raise NotExistent(f'{code_string} could not be resolved to a valid code label')
        except MultipleObjectsError:
            raise MultipleObjectsError(f'{code_string} could not be uniquely resolved')

    @classmethod
    def list_for_plugin(cls, plugin, labels=True, backend=None):
        """
        Return a list of valid code strings for a given plugin.

        :param plugin: The string of the plugin.
        :param labels: if True, return a list of code names, otherwise
          return the code PKs (integers).
        :return: a list of string, with the code names if labels is True,
          otherwise a list of integers with the code PKs.
        """
        from aiida.orm.querybuilder import QueryBuilder
        query = QueryBuilder(backend=backend)
        query.append(cls, filters={'attributes.input_plugin': {'==': plugin}})
        valid_codes = query.all(flat=True)

        if labels:
            return [c.label for c in valid_codes]

        return [c.pk for c in valid_codes]

    def _validate(self):
        super()._validate()

        # do bunch of validate here
        
        # if self.is_local() is None:
        #     raise exceptions.ValidationError('You did not set whether the code is local or remote')

        # if self.is_local():
        #     if not self.get_local_executable():
        #         raise exceptions.ValidationError(
        #             'You have to set which file is the local executable '
        #             'using the set_exec_filename() method'
        #         )
        #     if self.get_local_executable() not in self.list_object_names():
        #         raise exceptions.ValidationError(
        #             f"The local executable '{self.get_local_executable()}' is not in the list of files of this code"
        #         )
        # else:
        #     if self.list_object_names():
        #         raise exceptions.ValidationError('The code is remote but it has files inside')
        #     if not self.get_remote_computer():
        #         raise exceptions.ValidationError('You did not specify a remote computer')
        #     if not self.get_remote_exec_path():
        #         raise exceptions.ValidationError('You did not specify a remote executable')

    def validate_remote_exec_path(self):
        """Validate the ``remote_exec_path`` attribute.

        Checks whether the executable exists on the remote computer if a transport can be opened to it. This method
        is intentionally not called in ``_validate`` as to allow the creation of ``Code`` instances whose computers can
        not yet be connected to and as to not require the overhead of opening transports in storing a new code.

        :raises `~aiida.common.exceptions.ValidationError`: if no transport could be opened or if the defined executable
            does not exist on the remote computer.
        """
        filepath = self.get_remote_exec_path()

        try:
            with override_log_level():  # Temporarily suppress noisy logging
                with self.computer.get_transport() as transport:
                    file_exists = transport.isfile(filepath)
        except Exception:  # pylint: disable=broad-except
            raise exceptions.ValidationError(
                'Could not connect to the configured computer to determine whether the specified executable exists.'
            )

        if not file_exists:
            raise exceptions.ValidationError(
                f'the provided remote absolute path `{filepath}` does not exist on the computer.'
            )

    def set_prepend_text(self, code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self.set_attribute('prepend_text', str(code))

    def get_prepend_text(self):
        """
        Return the code that will be put in the scheduler script before the
        execution, or an empty string if no pre-exec code was defined.
        """
        return self.get_attribute('prepend_text', '')

    def set_input_plugin_name(self, input_plugin):
        """
        Set the name of the default input plugin, to be used for the automatic
        generation of a new calculation.
        """
        if input_plugin is None:
            self.set_attribute('input_plugin', None)
        else:
            self.set_attribute('input_plugin', str(input_plugin))

    def get_input_plugin_name(self):
        """
        Return the name of the default input plugin (or None if no input plugin
        was set.
        """
        return self.get_attribute('input_plugin', None)

    def set_append_text(self, code):
        """
        Pass a string of code that will be put in the scheduler script after the
        execution of the code.
        """
        self.set_attribute('append_text', str(code))

    def get_append_text(self):
        """
        Return the postexec_code, or an empty string if no post-exec code was defined.
        """
        return self.get_attribute('append_text', '')

    def set_container_exec(self, computer, container_thing, image, container_exec_path):
        """
        Set the code as container
        """
        from aiida import orm
        from aiida.common.lang import type_check

        if not os.path.isabs(container_exec_path):
            raise ValueError('executable path must be an absolute path (on the remote machine)')

        type_check(computer, orm.Computer)
        self.computer = computer
        
        # self._set_container(container_thing)
        
        self.set_attribute('container_thing', container_thing)
        
        self.set_attribute('image', image)
        
        self.set_attribute('container_exec_path', container_exec_path)

    def get_container_exec_path(self):
        return self.get_attribute('container_exec_path', '')

    def get_remote_computer(self):
        return self.computer
    
    def get_image(self):
        """Get image name"""
        return self.get_attribute('image', '')
    
    def get_container_thing(self):
        return self.get_attribute('container_thing', '')


    # This should be _set_container method for setting container related info from container thing
    # def _set_remote(self):
    #     """
    #     Set the code as a 'remote' code, meaning that the code itself has no files attached,
    #     but only a location on a remote computer (with an absolute path of the executable on
    #     the remote computer).

    #     It also deletes the flags related to the local case (if any)
    #     """
    #     self.set_attribute('is_local', False)
    #     try:
    #         self.delete_attribute('local_executable')
    #     except AttributeError:
    #         pass

    # def is_local(self):
    #     """
    #     Return True if the code is 'local', False if it is 'remote' (see also documentation
    #     of the set_local and set_remote functions).
    #     """
    #     return self.get_attribute('is_local', None)

    def can_run_on(self, computer):
        """
        Return True if this code can run on the given computer (in the future: if there is corresponting container technology run on there), False otherwise.
        
        TODO: add filters to mask the remote machines on which a local code can run.
        """
        from aiida import orm
        from aiida.common.lang import type_check
        
        # TODO the check for the container code is more complex
        type_check(computer, orm.Computer)
        return computer.id == self.get_remote_computer().id

    def get_builder(self):
        """Create and return a new `ProcessBuilder` for the `CalcJob` class of the plugin configured for this code.

        The configured calculation plugin class is defined by the `get_input_plugin_name` method.

        .. note:: it also sets the ``builder.code`` value.

        :return: a `ProcessBuilder` instance with the `code` input already populated with ourselves
        :raise aiida.common.EntryPointError: if the specified plugin does not exist.
        :raise ValueError: if no default plugin was specified.
        """
        from aiida.plugins import CalculationFactory

        plugin_name = self.get_input_plugin_name()

        if plugin_name is None:
            raise ValueError('no default calculation input plugin specified for this code')

        try:
            process_class = CalculationFactory(plugin_name)
        except exceptions.EntryPointError:
            raise exceptions.EntryPointError(f'the calculation entry point `{plugin_name}` could not be loaded')

        builder = process_class.get_builder()
        builder.code = self

        return builder

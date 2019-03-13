# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import six

from aiida.common.exceptions import (ValidationError, MissingPluginError, InputValidationError)

from .data import Data

DEPRECATION_DOCS_URL = 'http://aiida-core.readthedocs.io/en/latest/concepts/processes.html#the-process-builder'

__all__ = ('Code',)


class Code(Data):
    """
    A code entity.
    It can either be 'local', or 'remote'.

    * Local code: it is a collection of files/dirs (added using the add_path() method), where one \
    file is flagged as executable (using the set_local_executable() method).

    * Remote code: it is a pair (remotecomputer, remotepath_of_executable) set using the \
    set_remote_computer_exec() method.

    For both codes, one can set some code to be executed right before or right after
    the execution of the code, using the set_preexec_code() and set_postexec_code()
    methods (e.g., the set_preexec_code() can be used to load specific modules required
    for the code to be run).
    """

    def __init__(self, remote_computer_exec=None, local_executable=None, input_plugin_name=None, files=None, **kwargs):
        super(Code, self).__init__(**kwargs)

        if remote_computer_exec and local_executable:
            raise ValueError('cannot set `remote_computer_exec` and `local_executable` at the same time')

        if remote_computer_exec:
            self.set_remote_computer_exec(remote_computer_exec)

        if local_executable:
            self.set_local_executable(local_executable)

        if input_plugin_name:
            self.set_input_plugin_name(input_plugin_name)

        if files:
            self.set_files(files)

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

    def set_files(self, files):
        """
        Given a list of filenames (or a single filename string),
        add it to the path (all at level zero, i.e. without folders).
        Therefore, be careful for files with the same name!

        :todo: decide whether to check if the Code must be a local executable
             to be able to call this function.
        """

        if isinstance(files, six.string_types):
            files = [files]

        for filename in files:
            if os.path.isfile(filename):
                with io.open(filename, 'rb') as handle:
                    self.put_object_from_filelike(handle, os.path.split(filename)[1], 'wb', encoding=None)

    def __str__(self):
        local_str = "Local" if self.is_local() else "Remote"
        computer_str = self.get_computer_name()
        return "{} code '{}' on {}, pk: {}, uuid: {}".format(local_str, self.label, computer_str, self.pk, self.uuid)

    def get_computer_name(self):
        """Get name of this code's computer."""

        if self.is_local():
            computer_str = "repository"
        else:
            if self.computer is not None:
                computer_str = self.computer.name
            else:
                computer_str = "[unknown]"

        return computer_str

    @property
    def full_label(self):
        """Get full label of this code.

        Returns label of the form <code-label>@<computer-name>.
        """
        return '{}@{}'.format(self.label, self.get_computer_name())

    def relabel(self, new_label, raise_error=True):
        """Relabel this code.

        :param new_label: new code label
        :param raise_error: Set to False in order to return a list of errors
            instead of raising them.
        """
        suffix = '@{}'.format(self.get_computer_name())
        if new_label.endswith(suffix):
            new_label = new_label[:-len(suffix)]

        if '@' in new_label:
            msg = "Code labels must not contain the '@' symbol"
            if raise_error:
                raise InputValidationError(msg)
            else:
                return InputValidationError(msg)

        self.label = new_label

    def get_description(self):
        """Return a string description of this Code instance.

        :return: string description of this Code instance
        """
        return '{}'.format(self.label)

    @classmethod
    def get_code_helper(cls, label, machinename=None):
        """
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely
            a code
        """
        from aiida.common.exceptions import (NotExistent, MultipleObjectsError, InputValidationError)
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computers import Computer

        qb = QueryBuilder()
        qb.append(cls, filters={'label': {'==': label}}, project=['*'], tag='code')
        if machinename:
            qb.append(Computer, filters={'name': {'==': machinename}}, with_node='code')

        if qb.count() == 0:
            raise NotExistent("'{}' is not a valid code name.".format(label))
        elif qb.count() > 1:
            codes = [_ for [_] in qb.all()]
            retstr = ("There are multiple codes with label '{}', having IDs: ".format(label))
            retstr += ", ".join(sorted([str(c.pk) for c in codes])) + ".\n"
            retstr += ("Relabel them (using their ID), or refer to them with their ID.")
            raise MultipleObjectsError(retstr)
        else:
            return qb.first()[0]

    @classmethod
    def get(cls, pk=None, label=None, machinename=None):
        """
        Get a Computer object with given identifier string, that can either be
        the numeric ID (pk), or the label (and computername) (if unique).

        :param pk: the numeric ID (pk) for code
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely
            a code
        :raise aiida.common.InputValidationError: if neither a pk nor a label was passed in
        """
        from aiida.common.exceptions import (NotExistent, MultipleObjectsError, InputValidationError)
        from aiida.orm.utils import load_code

        # first check if code pk is provided
        if (pk):
            code_int = int(pk)
            try:
                return load_code(pk=code_int)
            except NotExistent:
                raise ValueError("{} is not valid code pk".format(pk))
            except MultipleObjectsError:
                raise MultipleObjectsError("More than one code in the DB with pk='{}'!".format(pk))

        # check if label (and machinename) is provided
        elif (label != None):
            return cls.get_code_helper(label, machinename)

        else:
            raise InputValidationError("Pass either pk or code label (and machinename)")

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
        :raise aiida.common.InputValidationError: if code_string is not of string type

        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError, InputValidationError

        try:
            label, sep, machinename = code_string.partition('@')
        except AttributeError as exception:
            raise InputValidationError("the provided code_string is not of valid string type")

        try:
            return cls.get_code_helper(label, machinename)
        except NotExistent:
            raise NotExistent("{} could not be resolved to a valid code label".format(code_string))
        except MultipleObjectsError:
            raise MultipleObjectsError("{} could not be uniquely resolved".format(code_string))

    @classmethod
    def list_for_plugin(cls, plugin, labels=True):
        """
        Return a list of valid code strings for a given plugin.

        :param plugin: The string of the plugin.
        :param labels: if True, return a list of code names, otherwise
          return the code PKs (integers).
        :return: a list of string, with the code names if labels is True,
          otherwise a list of integers with the code PKs.
        """
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(cls, filters={'attributes.input_plugin': {'==': plugin}})
        valid_codes = [_ for [_] in qb.all()]

        if labels:
            return [c.label for c in valid_codes]
        else:
            return [c.pk for c in valid_codes]

    def _validate(self):
        super(Code, self)._validate()

        if self.is_local() is None:
            raise ValidationError("You did not set whether the code is local or remote")

        if self.is_local():
            if not self.get_local_executable():
                raise ValidationError("You have to set which file is the local executable "
                                      "using the set_exec_filename() method")
                # c[1] is True if the element is a file
            if self.get_local_executable() not in self.list_object_names():
                raise ValidationError("The local executable '{}' is not in the list of "
                                      "files of this code".format(self.get_local_executable()))
        else:
            if self.list_object_names():
                raise ValidationError("The code is remote but it has files inside")
            if not self.get_remote_computer():
                raise ValidationError("You did not specify a remote computer")
            if not self.get_remote_exec_path():
                raise ValidationError("You did not specify a remote executable")

    def set_prepend_text(self, code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self.set_attribute('prepend_text', six.text_type(code))

    def get_prepend_text(self):
        """
        Return the code that will be put in the scheduler script before the
        execution, or an empty string if no pre-exec code was defined.
        """
        return self.get_attribute('prepend_text', u"")

    def set_input_plugin_name(self, input_plugin):
        """
        Set the name of the default input plugin, to be used for the automatic
        generation of a new calculation.
        """
        if input_plugin is None:
            self.set_attribute('input_plugin', None)
        else:
            self.set_attribute('input_plugin', six.text_type(input_plugin))

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
        self.set_attribute('append_text', six.text_type(code))

    def get_append_text(self):
        """
        Return the postexec_code, or an empty string if no post-exec code was defined.
        """
        return self.get_attribute('append_text', u"")

    def set_local_executable(self, exec_name):
        """
        Set the filename of the local executable.
        Implicitly set the code as local.
        """
        self._set_local()
        self.set_attribute('local_executable', exec_name)

    def get_local_executable(self):
        return self.get_attribute('local_executable', u"")

    def set_remote_computer_exec(self, remote_computer_exec):
        """
        Set the code as remote, and pass the computer on which it resides
        and the absolute path on that computer.

        :param remote_computer_exec: a tuple (computer, remote_exec_path), where computer is a aiida.orm.Computer and
            remote_exec_path is the absolute path of the main executable on remote computer.
        """
        from aiida import orm
        from aiida.common.lang import type_check

        if (not isinstance(remote_computer_exec, (list, tuple)) or len(remote_computer_exec) != 2):
            raise ValueError("remote_computer_exec must be a list or tuple "
                             "of length 2, with machine and executable "
                             "name")

        computer, remote_exec_path = tuple(remote_computer_exec)

        if not os.path.isabs(remote_exec_path):
            raise ValueError("exec_path must be an absolute path (on the remote machine)")

        type_check(computer, orm.Computer)

        self._set_remote()
        self.computer = computer
        self.set_attribute('remote_exec_path', remote_exec_path)

    def get_remote_exec_path(self):
        if self.is_local():
            raise ValueError("The code is local")
        return self.get_attribute('remote_exec_path', "")

    def get_remote_computer(self):
        if self.is_local():
            raise ValueError("The code is local")

        return self.computer

    def _set_local(self):
        """
        Set the code as a 'local' code, meaning that all the files belonging to the code
        will be copied to the cluster, and the file set with set_exec_filename will be
        run.

        It also deletes the flags related to the local case (if any)
        """
        self.set_attribute('is_local', True)
        self.computer = None
        try:
            self.delete_attribute('remote_exec_path')
        except AttributeError:
            pass

    def _set_remote(self):
        """
        Set the code as a 'remote' code, meaning that the code itself has no files attached,
        but only a location on a remote computer (with an absolute path of the executable on
        the remote computer).

        It also deletes the flags related to the local case (if any)
        """
        self.set_attribute('is_local', False)
        try:
            self.delete_attribute('local_executable')
        except AttributeError:
            pass

    def is_local(self):
        """
        Return True if the code is 'local', False if it is 'remote' (see also documentation
        of the set_local and set_remote functions).
        """
        return self.get_attribute('is_local', None)

    def can_run_on(self, computer):
        """
        Return True if this code can run on the given computer, False otherwise.

        Local codes can run on any machine; remote codes can run only on the machine
        on which they reside.

        TODO: add filters to mask the remote machines on which a local code can run.
        """
        from aiida import orm
        from aiida.common.lang import type_check

        if self.is_local():
            return True

        type_check(computer, orm.Computer)
        return computer.id == self.get_remote_computer().id

    def get_execname(self):
        """
        Return the executable string to be put in the script.
        For local codes, it is ./LOCAL_EXECUTABLE_NAME
        For remote codes, it is the absolute path to the executable.
        """
        if self.is_local():
            return u"./{}".format(self.get_local_executable())
        else:
            return self.get_remote_exec_path()

    def get_builder(self):
        """
        Create and return a new ProcessBuilder for the default Calculation
        plugin, as obtained by the self.get_input_plugin_name() method.

        :note: it also sets the ``builder.code`` value.

        :raise aiida.common.MissingPluginError: if the specified plugin does not exist.
        :raise ValueError: if no default plugin was specified.

        :return:
        """
        from aiida.plugins import CalculationFactory
        plugin_name = self.get_input_plugin_name()
        if plugin_name is None:
            raise ValueError("You did not specify a default input plugin for this code")
        try:
            C = CalculationFactory(plugin_name)
        except MissingPluginError:
            raise MissingPluginError("The input_plugin name for this code is "
                                     "'{}', but it is not an existing plugin"
                                     "name".format(plugin_name))

        builder = C.get_builder()
        # Setup the code already
        builder.code = self

        return builder

    def full_text_info(self, verbose=False):
        """
        Return a (multiline) string with a human-readable detailed information on this computer
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('This method has been deprecated and will be renamed to get_full_text_info() in AiiDA v1.0', DeprecationWarning)
        return self.get_full_text_info(verbose=verbose)

    def get_full_text_info(self, verbose=False):
        """
        Return a (multiline) string with a human-readable detailed information on this computer
        """
        result = []
        result.append(['PK', self.pk])
        result.append(['UUID', self.uuid])
        result.append(['Label', self.label])
        result.append(['Description', self.description])
        result.append(['Default plugin', self.get_input_plugin_name()])

        if verbose:
            result.append(['Calculations', len(self.get_outgoing().all())])

        if self.is_local():
            result.append(['Type', 'local'])
            result.append(['Exec name', self.get_execname()])
            result.append(['List of files/folders:', ''])
            for fname in self.list_object_names():
                if self._repository._get_folder_pathsubfolder.isdir(fname):
                    result.append(['directory', fname])
                else:
                    result.append(['file', fname])
        else:
            result.append(['Type', 'remote'])
            result.append(['Remote machine', self.get_remote_computer().name])
            result.append(['Remote absolute path', self.get_remote_exec_path()])

        if self.get_prepend_text().strip():
            result.append(['Prepend text', ''])
            for line in self.get_prepend_text().split('\n'):
                result.append(['', line])
        else:
            result.append(['Prepend text', 'No prepend text'])

        if self.get_append_text().strip():
            result.append(['Append text', ''])
            for line in self.get_append_text().split('\n'):
                result.append(['', line])
        else:
            result.append(['Append text', 'No append text'])

        return result

    @classmethod
    def setup(cls, **kwargs):
        # raise NotImplementedError
        from aiida.cmdline.commands.code import CodeInputValidationClass
        code = CodeInputValidationClass().set_and_validate_from_code(kwargs)

        try:
            code.store()
        except ValidationError as exc:
            raise ValidationError("Unable to store the computer: {}.".format(exc))
        return code

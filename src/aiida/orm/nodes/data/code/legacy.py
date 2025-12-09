###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin represeting an executable code to be wrapped and called through a `CalcJob` plugin."""

import os
import pathlib
import typing as t

from aiida.common import exceptions
from aiida.common.log import override_log_level
from aiida.common.pydantic import MetadataField
from aiida.common.warnings import warn_deprecation
from aiida.orm import Computer

from .abstract import AbstractCode

__all__ = ('Code',)


class Code(AbstractCode):
    """A code entity.
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

    class AttributesModel(AbstractCode.AttributesModel):
        prepend_text: str = MetadataField(
            '',
            description='The code that will be put in the scheduler script before the execution of the code',
        )
        append_text: str = MetadataField(
            '',
            description='The code that will be put in the scheduler script after the execution of the code',
        )
        input_plugin: t.Optional[str] = MetadataField(
            description='The name of the input plugin to be used for this code'
        )
        local_executable: t.Optional[str] = MetadataField(description='Path to a local executable')
        remote_exec_path: t.Optional[str] = MetadataField(description='Remote path to executable')
        is_local: t.Optional[bool] = MetadataField(description='Whether the code is local or remote')

    def __init__(self, remote_computer_exec=None, local_executable=None, input_plugin_name=None, files=None, **kwargs):
        super().__init__(**kwargs)

        # The ``_EMIT_CODE_DEPRECATION_WARNING`` attribute is set in subclasses to avoid the deprecation message below
        # is also shown when they are instantiated, since they are not deprecated.
        if getattr(self, '_EMIT_CODE_DEPRECATION_WARNING', True):
            warn_deprecation(
                'The `Code` class is deprecated. To create an instance, use the '
                '`aiida.orm.nodes.data.code.installed.InstalledCode` or '
                '`aiida.orm.nodes.data.code.portable.PortableCode` for a "remote" or "local" code, respectively. If '
                'you are using this class to compare type, e.g. in '
                '`isinstance`, use `aiida.orm.nodes.data.code.abstract.AbstractCode`.',
                version=3,
            )

        if remote_computer_exec and local_executable:
            raise ValueError('cannot set `remote_computer_exec` and `local_executable` at the same time')

        if remote_computer_exec:
            warn_deprecation(
                'The `Code` plugin is deprecated, use the `InstalledCode` (`core.code.remote`) instead.', 3
            )
            self.set_remote_computer_exec(remote_computer_exec)

        if local_executable:
            warn_deprecation('The `Code` plugin is deprecated, use the `PortableCode` (`core.code.local`) instead.', 3)
            self.set_local_executable(local_executable)

        if input_plugin_name:
            self.set_input_plugin_name(input_plugin_name)

        if files:
            self.set_files(files)

    HIDDEN_KEY = 'hidden'

    def can_run_on_computer(self, computer: Computer) -> bool:
        """Return whether the code can run on a given computer.

        :param computer: The computer.
        :return: ``True`` if the code can run on ``computer``, ``False`` otherwise.
        """
        from aiida import orm
        from aiida.common.lang import type_check

        if self.is_local():
            return True

        type_check(computer, orm.Computer)
        return computer.pk == self.get_remote_computer().pk

    def get_executable(self) -> pathlib.PurePath:
        """Return the executable that the submission script should execute to run the code.

        :return: The executable to be called in the submission script.
        """
        if self.is_local():
            exec_path = f'./{self.get_local_executable()}'
        else:
            exec_path = self.get_remote_exec_path()

        return pathlib.PurePath(exec_path)

    def hide(self):
        """Hide the code (prevents from showing it in the verdi code list)"""
        warn_deprecation('`Code.hide` property is deprecated, use the `Code.is_hidden` property instead.', version=3)
        self.is_hidden = True

    def reveal(self):
        """Reveal the code (allows to show it in the verdi code list)
        By default, it is revealed
        """
        warn_deprecation('`Code.reveal` property is deprecated, use the `Code.is_hidden` property instead.', version=3)
        self.is_hidden = False

    @property
    def hidden(self):
        """Determines whether the Code is hidden or not"""
        warn_deprecation('`Code.hidden` property is deprecated, use the `Code.is_hidden` property instead.', version=3)
        return self.is_hidden

    def set_files(self, files):
        """Given a list of filenames (or a single filename string),
        add it to the path (all at level zero, i.e. without folders).
        Therefore, be careful for files with the same name!

        :todo: decide whether to check if the Code must be a local executable
             to be able to call this function.
        """
        if isinstance(files, str):
            files = [files]

        for filename in files:
            if os.path.isfile(filename):
                with open(filename, 'rb') as handle:
                    self.base.repository.put_object_from_filelike(handle, os.path.split(filename)[1])

    def __str__(self):
        if self.computer is None:
            return f"Local code '{self.label}' pk: {self.pk}, uuid: {self.uuid}"

        return f"Remote code '{self.label}' on {self.computer.label} pk: {self.pk}, uuid: {self.uuid}"

    def get_computer_label(self):
        """Get label of this code's computer."""
        warn_deprecation(
            '`Code.get_computer_label` method is deprecated, use the `InstalledCode.computer.label` property instead.',
            version=3,
        )
        return 'repository' if self.computer is None else self.computer.label

    @property
    def full_label(self):
        """Get full label of this code.

        Returns label of the form <code-label>@<computer-name>.
        """
        return f'{self.label}@{"repository" if self.computer is None else self.computer.label}'

    def relabel(self, new_label):
        """Relabel this code.

        :param new_label: new code label
        """
        warn_deprecation('`Code.relabel` method is deprecated, use the `label` property instead.', version=3)
        if self.computer is not None:
            suffix = f'@{self.computer.label}'
            if new_label.endswith(suffix):
                new_label = new_label[: -len(suffix)]

        self.label = new_label

    def get_description(self):
        """Return a string description of this Code instance.

        :return: string description of this Code instance
        """
        return self.full_label

    @classmethod
    def get_code_helper(cls, label, machinename=None, backend=None):
        """:param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely
            a code
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.querybuilder import QueryBuilder

        warn_deprecation(
            '`Code.get_code_helper` classmethod is deprecated, use `aiida.orm.load_code` instead.', version=3
        )

        query = QueryBuilder(backend=backend)
        query.append(cls, filters={'label': label}, project='*', tag='code')
        if machinename:
            query.append(Computer, filters={'label': machinename}, with_node='code')

        if query.count() == 0:
            raise NotExistent(f"'{label}' is not a valid code label.")
        elif query.count() > 1:
            codes = query.all(flat=True)
            retstr = f"There are multiple codes with label '{label}', having IDs: "
            retstr += f'{", ".join(sorted([str(c.pk) for c in codes]))}.\n'
            retstr += 'Relabel them (using their ID), or refer to them with their ID.'
            raise MultipleObjectsError(retstr)
        else:
            result = query.first()
            if not result:
                raise NotExistent(f"code '{label}' does not exist.")

            return result[0]

    @classmethod
    def get(cls, pk=None, label=None, machinename=None):  # type: ignore[override]
        """Get a Computer object with given identifier string, that can either be
        the numeric ID (pk), or the label (and computername) (if unique).

        :param pk: the numeric ID (pk) for code
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise aiida.common.NotExistent: if no code identified by the given string is found
        :raise aiida.common.MultipleObjectsError: if the string cannot identify uniquely a code
        :raise ValueError: if neither a pk nor a label was passed in
        """
        from aiida.orm.utils import load_code

        warn_deprecation('`Code.get` classmethod is deprecated, use `aiida.orm.load_code` instead.', version=3)

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
        """Get a Computer object with given identifier string in the format
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

        warn_deprecation(
            '`Code.get_from_string` classmethod is deprecated, use `aiida.orm.load_code` instead.', version=3
        )

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
        """Return a list of valid code strings for a given plugin.

        :param plugin: The string of the plugin.
        :param labels: if True, return a list of code names, otherwise
          return the code PKs (integers).
        :return: a list of string, with the code names if labels is True,
          otherwise a list of integers with the code PKs.
        """
        from aiida.orm.querybuilder import QueryBuilder

        warn_deprecation('`Code.list_for_plugin` classmethod has been deprecated, there is no replacement.', version=3)

        query = QueryBuilder(backend=backend)
        query.append(cls, filters={'attributes.input_plugin': {'==': plugin}})
        valid_codes = query.all(flat=True)

        if labels:
            return [c.label for c in valid_codes]

        return [c.pk for c in valid_codes]

    def _validate(self):
        super()._validate()

        if self.is_local() is None:
            raise exceptions.ValidationError('You did not set whether the code is local or remote')

        if self.is_local():
            if not self.get_local_executable():
                raise exceptions.ValidationError(
                    'You have to set which file is the local executable using the set_exec_filename() method'
                )
            if self.get_local_executable() not in self.base.repository.list_object_names():
                raise exceptions.ValidationError(
                    f"The local executable '{self.get_local_executable()}' is not in the list of files of this code"
                )
        else:
            if self.base.repository.list_object_names():
                raise exceptions.ValidationError('The code is remote but it has files inside')
            if not self.get_remote_computer():
                raise exceptions.ValidationError('You did not specify a remote computer')
            if not self.get_remote_exec_path():
                raise exceptions.ValidationError('You did not specify a remote executable')

    def validate_remote_exec_path(self):
        """Validate the ``remote_exec_path`` attribute.

        Checks whether the executable exists on the remote computer if a transport can be opened to it. This method
        is intentionally not called in ``_validate`` as to allow the creation of ``Code`` instances whose computers can
        not yet be connected to and as to not require the overhead of opening transports in storing a new code.

        :raises `~aiida.common.exceptions.ValidationError`: if no transport could be opened or if the defined executable
            does not exist on the remote computer.
        """
        warn_deprecation(
            '`Code.validate_remote_exec_path` method is deprecated, use the '
            '`InstalledCode.validate_filepath_executable` property instead.',
            version=3,
        )
        filepath = self.get_remote_exec_path()

        if self.computer is None:
            raise exceptions.ValidationError('checking the remote exec path is not available for a local code.')

        try:
            with override_log_level():  # Temporarily suppress noisy logging
                with self.computer.get_transport() as transport:
                    file_exists = transport.isfile(filepath)
        except Exception:
            raise exceptions.ValidationError(
                'Could not connect to the configured computer to determine whether the specified executable exists.'
            )

        if not file_exists:
            raise exceptions.ValidationError(
                f'the provided remote absolute path `{filepath}` does not exist on the computer.'
            )

    def set_prepend_text(self, code):
        """Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        warn_deprecation(
            '`Code.set_prepend_text` method is deprecated, use the `prepend_text` property instead.', version=3
        )
        self.prepend_text = code

    def get_prepend_text(self) -> str:
        """Return the code that will be put in the scheduler script before the
        execution, or an empty string if no pre-exec code was defined.
        """
        warn_deprecation(
            '`Code.get_prepend_text` method is deprecated, use the `prepend_text` property instead.', version=3
        )
        return self.prepend_text

    def set_input_plugin_name(self, input_plugin):
        """Set the name of the default input plugin, to be used for the automatic
        generation of a new calculation.
        """
        warn_deprecation(
            '`Code.set_input_plugin_name` method is deprecated, use the `default_calc_job_plugin` property instead.',
            version=3,
        )
        self.default_calc_job_plugin = input_plugin

    def get_input_plugin_name(self):
        """Return the name of the default input plugin (or None if no input plugin
        was set.
        """
        warn_deprecation(
            '`Code.get_input_plugin_name` method is deprecated, use the `default_calc_job_plugin` property instead.',
            version=3,
        )
        return self.default_calc_job_plugin

    def set_use_double_quotes(self, use_double_quotes: bool):
        """Set whether the command line invocation of this code should be escaped with double quotes.

        :param use_double_quotes: True if to escape with double quotes, False otherwise.
        """
        warn_deprecation(
            '`Code.set_use_double_quotes` method is deprecated, use the `use_double_quotes` property instead.',
            version=3,
        )
        self.use_double_quotes = use_double_quotes

    def get_use_double_quotes(self) -> bool:
        """Return whether the command line invocation of this code should be escaped with double quotes.

        :returns: True if to escape with double quotes, False otherwise which is also the default.
        """
        warn_deprecation(
            '`Code.get_use_double_quotes` method is deprecated, use the `use_double_quotes` property instead.',
            version=3,
        )
        return self.use_double_quotes

    def set_append_text(self, code):
        """Pass a string of code that will be put in the scheduler script after the
        execution of the code.
        """
        warn_deprecation(
            '`Code.set_append_text` method is deprecated, use the `append_text` property instead.', version=3
        )
        self.append_text = code

    def get_append_text(self):
        """Return the postexec_code, or an empty string if no post-exec code was defined."""
        warn_deprecation(
            '`Code.get_append_text` method is deprecated, use the `append_text` property instead.', version=3
        )
        return self.append_text

    def set_local_executable(self, exec_name):
        """Set the filename of the local executable.
        Implicitly set the code as local.
        """
        warn_deprecation('`Code.set_local_executable` method is deprecated, use `PortableCode`.', version=3)

        self._set_local()
        self.filepath_executable = exec_name

    def get_local_executable(self):
        """Return the local executable."""
        warn_deprecation(
            '`Code.get_local_executable` method is deprecated, use `PortableCode.filepath_executable` instead.',
            version=3,
        )
        return self.filepath_executable

    def set_remote_computer_exec(self, remote_computer_exec):
        """Set the code as remote, and pass the computer on which it resides
        and the absolute path on that computer.

        :param remote_computer_exec: a tuple (computer, remote_exec_path), where computer is a aiida.orm.Computer and
            remote_exec_path is the absolute path of the main executable on remote computer.
        """
        from aiida import orm
        from aiida.common.lang import type_check

        warn_deprecation('`Code.set_remote_computer_exec` method is deprecated, use `InstalledCode`.', version=3)

        if not isinstance(remote_computer_exec, (list, tuple)) or len(remote_computer_exec) != 2:
            raise ValueError(
                'remote_computer_exec must be a list or tuple of length 2, with machine and executable name'
            )

        computer, remote_exec_path = tuple(remote_computer_exec)

        if not os.path.isabs(remote_exec_path):
            raise ValueError('exec_path must be an absolute path (on the remote machine)')

        type_check(computer, orm.Computer)

        self._set_remote()
        self.computer = computer
        self.base.attributes.set('remote_exec_path', remote_exec_path)

    def get_remote_exec_path(self):
        """Return the ``remote_exec_path`` attribute."""
        warn_deprecation(
            '`Code.get_remote_exec_path` method is deprecated, use `InstalledCode.filepath_executable` instead.',
            version=3,
        )
        if self.is_local():
            raise ValueError('The code is local')
        return self.base.attributes.get('remote_exec_path', '')

    def get_remote_computer(self):
        """Return the remote computer associated with this code."""
        warn_deprecation(
            '`Code.get_remote_computer` method is deprecated, use the `computer` attribute instead.', version=3
        )
        if self.is_local():
            raise ValueError('The code is local')

        return self.computer

    def _set_local(self):
        """Set the code as a 'local' code, meaning that all the files belonging to the code
        will be copied to the cluster, and the file set with set_exec_filename will be
        run.

        It also deletes the flags related to the local case (if any)
        """
        self.base.attributes.set('is_local', True)
        self.computer = None
        try:
            self.base.attributes.delete('remote_exec_path')
        except AttributeError:
            pass

    def _set_remote(self):
        """Set the code as a 'remote' code, meaning that the code itself has no files attached,
        but only a location on a remote computer (with an absolute path of the executable on
        the remote computer).

        It also deletes the flags related to the local case (if any)
        """
        self.base.attributes.set('is_local', False)
        try:
            self.base.attributes.delete('local_executable')
        except AttributeError:
            pass

    def is_local(self):
        """Return True if the code is 'local', False if it is 'remote' (see also documentation
        of the set_local and set_remote functions).
        """
        warn_deprecation(
            '`Code.is_local` method is deprecated, use a `PortableCode` instance and check the type.', version=3
        )
        return self.base.attributes.get('is_local', None)

    def can_run_on(self, computer):
        """Return True if this code can run on the given computer, False otherwise.

        Local codes can run on any machine; remote codes can run only on the machine
        on which they reside.

        TODO: add filters to mask the remote machines on which a local code can run.
        """
        from aiida import orm
        from aiida.common.lang import type_check

        warn_deprecation('`Code.can_run_on` method is deprecated, use `can_run_on_computer` instead.', version=3)

        if self.is_local():
            return True

        type_check(computer, orm.Computer)
        return computer.pk == self.get_remote_computer().pk

    def get_execname(self):
        """Return the executable string to be put in the script.
        For local codes, it is ./LOCAL_EXECUTABLE_NAME
        For remote codes, it is the absolute path to the executable.
        """
        warn_deprecation('`Code.get_execname` method is deprecated, use `get_executable` instead.', version=3)
        return str(self.get_executable())

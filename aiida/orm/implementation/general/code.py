# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
from abc import abstractmethod
from aiida.orm.implementation import Node
from aiida.common.exceptions import (ValidationError, MissingPluginError)
from aiida.common.links import LinkType
from aiida.orm.mixins import SealableWithUpdatableAttributes
from aiida.common.utils import abstractclassmethod



class AbstractCode(SealableWithUpdatableAttributes, Node):
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

    def _init_internal_params(self):
        """
        This function is called by the init method
        """
        self._updatable_attributes = \
            ('input_plugin', 'append_text', 'prepend_text', 'hidden')

        self._set_incompatibilities = [
            ('remote_computer_exec', 'local_executable')]

    def _hide(self):
        """
        Hide the code (prevents from showing it in the verdi code list)
        """
        self._set_attr("hidden", True)

    def _reveal(self):
        """
        Reveal the code (allows to show it in the verdi code list)
        By default, it is revealed
        """
        self._set_attr("hidden", False)

    def _is_hidden(self):
        """
        Determines whether the Code is hidden or not
        """
        return self.get_attr('hidden', False)

    def set_files(self, files):
        """
        Given a list of filenames (or a single filename string),
        add it to the path (all at level zero, i.e. without folders).
        Therefore, be careful for files with the same name!

        :todo: decide whether to check if the Code must be a local executable
             to be able to call this function.
        """

        if isinstance(files, basestring):
            files = [files]
        for f in files:
            self.add_path(f, os.path.split(f)[1])

    def __str__(self):
        local_str = "Local" if self.is_local() else "Remote"
        if self.is_local():
            computer_str = "repository"
        else:
            if self.get_computer() is not None:
                computer_str = self.get_computer().name
            else:
                computer_str = "[unknown]"

        return "{} code '{}' on {}, pk: {}, uuid: {}".format(local_str,
                                                             self.label,
                                                             computer_str,
                                                             self.pk, self.uuid)

    @classmethod
    def get_code_helper(cls, label, machinename=None):
        """
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise NotExistent: if no code identified by the given string is found
        :raise MultipleObjectsError: if the string cannot identify uniquely
            a code
        """
        from aiida.common.exceptions import (NotExistent, MultipleObjectsError,
                                             InputValidationError)
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.computer import Computer

        qb = QueryBuilder()
        qb.append(cls, filters={'label': {'==': label}},
                  project=['*'], tag='code')
        if machinename:
            qb.append(Computer, filters={'name': {'==': machinename}},
                  computer_of='code')

        if qb.count() == 0:
            raise NotExistent("'{}' is not a valid code "
                              "name.".format(label))
        elif qb.count() > 1:
            codes = [_ for [_] in qb.all()]
            retstr = ("There are multiple codes with label '{}', "
                      "having IDs: ".format(label))
            retstr += ", ".join(sorted([str(c.pk) for c in codes])) + ".\n"
            retstr += ("Relabel them (using their ID), or refer to them "
                       "with their ID.")
            raise MultipleObjectsError(retstr)
        else:
            return qb.first()[0]

    @abstractclassmethod
    def get(cls, pk=None, label=None, machinename=None):
        """
        Get a Computer object with given identifier string, that can either be
        the numeric ID (pk), or the label (and computername) (if unique).

        :param pk: the numeric ID (pk) for code
        :param label: the code label identifying the code to load
        :param machinename: the machine name where code is setup

        :raise NotExistent: if no code identified by the given string is found
        :raise MultipleObjectsError: if the string cannot identify uniquely
            a code
        :raise InputValidationError: if neither a pk nor a label was passed in
        """
        from aiida.common.exceptions import (NotExistent, MultipleObjectsError,
                                             InputValidationError)

        # first check if code pk is provided
        if(pk):
            code_int = int(pk)
            try:
                return cls.get_subclass_from_pk(code_int)
            except NotExistent:
                raise ValueError("{} is not valid code pk".format(pk))
            except MultipleObjectsError:
                raise MultipleObjectsError("More than one code in the DB "
                                           "with pk='{}'!".format(pk))

        # check if label (and machinename) is provided
        elif(label != None):
            return cls.get_code_helper(label, machinename)

        else:
            raise InputValidationError("Pass either pk or code label (and machinename)")


    @abstractclassmethod
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

        :raise NotExistent: if no code identified by the given string is found
        :raise MultipleObjectsError: if the string cannot identify uniquely
            a code
        :raise InputValidationError: if code_string is not of string type

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


    @abstractclassmethod
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

        super(AbstractCode, self)._validate()

        if self.is_local() is None:
            raise ValidationError("You did not set whether the code is local "
                                  "or remote")

        if self.is_local():
            if not self.get_local_executable():
                raise ValidationError(
                    "You have to set which file is the local executable "
                    "using the set_exec_filename() method")
                # c[1] is True if the element is a file
            if self.get_local_executable() not in self.get_folder_list():
                raise ValidationError(
                    "The local executable '{}' is not in the list of "
                    "files of this code".format(self.get_local_executable()))
        else:
            if self.get_folder_list():
                raise ValidationError(
                    "The code is remote but it has files inside")
            if not self.get_remote_computer():
                raise ValidationError("You did not specify a remote computer")
            if not self.get_remote_exec_path():
                raise ValidationError("You did not specify a remote executable")

    def add_link_from(self, src, label=None, link_type=LinkType.UNSPECIFIED):
        raise ValueError("A code node cannot have any input nodes")

    def _linking_as_output(self, dest, link_type):
        """
        Raise a ValueError if a link from self to dest is not allowed.

        An output of a code can only be a calculation
        """
        from aiida.orm.calculation import Calculation

        if not isinstance(dest, Calculation):
            raise ValueError(
                "The output of a code node can only be a calculation")

        return super(AbstractCode, self)._linking_as_output(dest, link_type)

    def set_prepend_text(self, code):
        """
        Pass a string of code that will be put in the scheduler script before the
        execution of the code.
        """
        self._set_attr('prepend_text', unicode(code))

    def get_prepend_text(self):
        """
        Return the code that will be put in the scheduler script before the
        execution, or an empty string if no pre-exec code was defined.
        """
        return self.get_attr('prepend_text', u"")

    def set_input_plugin_name(self, input_plugin):
        """
        Set the name of the default input plugin, to be used for the automatic
        generation of a new calculation.
        """
        if input_plugin is None:
            self._set_attr('input_plugin', None)
        else:
            self._set_attr('input_plugin', unicode(input_plugin))

    def get_input_plugin_name(self):
        """
        Return the name of the default input plugin (or None if no input plugin
        was set.
        """
        return self.get_attr('input_plugin', None)

    def set_append_text(self, code):
        """
        Pass a string of code that will be put in the scheduler script after the
        execution of the code.
        """
        self._set_attr('append_text', unicode(code))

    def get_append_text(self):
        """
        Return the postexec_code, or an empty string if no post-exec code was defined.
        """
        return self.get_attr('append_text', u"")

    def set_local_executable(self, exec_name):
        """
        Set the filename of the local executable.
        Implicitly set the code as local.
        """
        self._set_local()
        self._set_attr('local_executable', exec_name)

    def get_local_executable(self):
        return self.get_attr('local_executable', u"")

    @abstractmethod
    def set_remote_computer_exec(self, remote_computer_exec):
        """
        Set the code as remote, and pass the computer on which it resides
        and the absolute path on that computer.

        Args:
            remote_computer_exec: a tuple (computer, remote_exec_path), where
              computer is a aiida.orm.Computer or an
              aiida.backends.djsite.db.models.DbComputer object, and
              remote_exec_path is the absolute path of the main executable on
              remote computer.
        """
        pass

    def get_remote_exec_path(self):
        if self.is_local():
            raise ValueError("The code is local")
        return self.get_attr('remote_exec_path', "")

    def get_remote_computer(self):
        if self.is_local():
            raise ValueError("The code is local")

        return self.get_computer()

    @abstractmethod
    def _set_local(self):
        """
        Set the code as a 'local' code, meaning that all the files belonging to the code
        will be copied to the cluster, and the file set with set_exec_filename will be
        run.

        It also deletes the flags related to the local case (if any)
        """
        pass

    def _set_remote(self):
        """
        Set the code as a 'remote' code, meaning that the code itself has no files attached,
        but only a location on a remote computer (with an absolute path of the executable on
        the remote computer).

        It also deletes the flags related to the local case (if any)
        """
        self._set_attr('is_local', False)
        try:
            self._del_attr('local_executable')
        except AttributeError:
            pass

    def is_local(self):
        """
        Return True if the code is 'local', False if it is 'remote' (see also documentation
        of the set_local and set_remote functions).
        """
        return self.get_attr('is_local', None)

    @abstractmethod
    def can_run_on(self, computer):
        """
        Return True if this code can run on the given computer, False otherwise.

        Local codes can run on any machine; remote codes can run only on the machine
        on which they reside.

        TODO: add filters to mask the remote machines on which a local code can run.
        """
        pass

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

    def new_calc(self, *args, **kwargs):
        """
        Create and return a new Calculation object (unstored) with the correct
        plugin subclass, as obtained by the self.get_input_plugin_name() method.

        Parameters are passed to the calculation __init__ method.

        :note: it also directly creates the link to this code (that will of
            course be cached, since the new node is not stored yet).

        :raise MissingPluginError: if the specified plugin does not exist.
        :raise ValueError: if no plugin was specified.
        """
        from aiida.orm.utils import CalculationFactory
        plugin_name = self.get_input_plugin_name()
        if plugin_name is None:
            raise ValueError("You did not specify an input plugin "
                             "for this code")

        try:
            C = CalculationFactory(plugin_name)

        except MissingPluginError:
            raise MissingPluginError("The input_plugin name for this code is "
                                     "'{}', but it is not an existing plugin"
                                     "name".format(plugin_name))

        # For remote codes, automatically set the computer,
        # unless explicitly set by the user
        if not self.is_local():
            if 'computer' not in kwargs:
                kwargs['computer'] = self.get_remote_computer()

        new_calc = C(*args, **kwargs)
        # I link to the code
        new_calc.use_code(self)
        return new_calc

    @property
    def full_text_info(self):
        """
        Return a (multiline) string with a human-readable detailed information
        on this computer.
        """

        ret_lines = []
        ret_lines.append(" * PK:             {}".format(self.pk))
        ret_lines.append(" * UUID:           {}".format(self.uuid))
        ret_lines.append(" * Label:          {}".format(self.label))
        ret_lines.append(" * Description:    {}".format(self.description))
        ret_lines.append(" * Default plugin: {}".format(
            self.get_input_plugin_name()))
        ret_lines.append(" * Used by:        {} calculations".format(
            len(self.get_outputs())))
        if self.is_local():
            ret_lines.append(" * Type:           {}".format("local"))
            ret_lines.append(
                " * Exec name:      {}".format(self.get_execname()))
            ret_lines.append(" * List of files/folders:")
            for fname in self._get_folder_pathsubfolder.get_content_list():
                ret_lines.append("   * [{}] {}".format(" dir" if
                                                       self._get_folder_pathsubfolder.isdir(
                                                           fname) else "file",
                                                       fname))
        else:
            ret_lines.append(" * Type:           {}".format("remote"))
            ret_lines.append(" * Remote machine: {}".format(
                self.get_remote_computer().name))
            ret_lines.append(" * Remote absolute path: ")
            ret_lines.append("   " + self.get_remote_exec_path())

        ret_lines.append(" * prepend text:")
        if self.get_prepend_text().strip():
            for l in self.get_prepend_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No prepend text.")
        ret_lines.append(" * append text:")
        if self.get_append_text().strip():
            for l in self.get_append_text().split('\n'):
                ret_lines.append("   {}".format(l))
        else:
            ret_lines.append("   # No append text.")

        return "\n".join(ret_lines)

    @classmethod
    def setup(cls, **kwargs):
        # raise NotImplementedError
        from aiida.cmdline.commands.code import CodeInputValidationClass
        code = CodeInputValidationClass().set_and_validate_from_code(kwargs)

        try:
            code.store()
        except ValidationError as e:
            raise ValidationError(
                "Unable to store the computer: {}.".format(e.message))
        return code


def delete_code(code):
    """
    Delete a code from the DB.
    Check before that there are no output nodes.

    NOTE! Not thread safe... Do not use with many users accessing the DB
    at the same time.

    Implemented as a function on purpose, otherwise complicated logic would be
    needed to set the internal state of the object after calling
    computer.delete().
    """
    raise NotImplementedError

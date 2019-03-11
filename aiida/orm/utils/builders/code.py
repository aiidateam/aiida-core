# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Manage code objects with lazy loading of the db env"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import enum
import os

from aiida.cmdline.utils.decorators import with_dbenv
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.common.utils import ErrorAccumulator


class CodeBuilder(object):  # pylint: disable=useless-object-inheritance
    """Build a code with validation of attribute combinations"""

    def __init__(self, **kwargs):
        self._err_acc = ErrorAccumulator(self.CodeValidationError)
        self._code_spec = {}

        # code_type must go first
        for key in ['code_type']:
            self.__setattr__(key, kwargs.pop(key))

        # then set the rest
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def validate(self, raise_error=True):
        self._err_acc.run(self.validate_code_type)
        self._err_acc.run(self.validate_upload)
        self._err_acc.run(self.validate_installed)
        return self._err_acc.result(raise_error=self.CodeValidationError if raise_error else False)

    @with_dbenv()
    def new(self):
        """Build and return a new code instance (not stored)"""
        self.validate()

        from aiida.orm import Code

        # Will be used at the end to check if all keys are known (those that are not None)
        passed_keys = set(k for k in self._code_spec.keys() if self._code_spec[k] is not None)
        used = set()

        if self._get_and_count('code_type', used) == self.CodeType.STORE_AND_UPLOAD:
            file_list = [
                os.path.realpath(os.path.join(self.code_folder, f))
                for f in os.listdir(self._get_and_count('code_folder', used))
            ]
            code = Code(local_executable=self._get_and_count('code_rel_path', used), files=file_list)
        else:
            code = Code(
                remote_computer_exec=(self._get_and_count('computer', used),
                                      self._get_and_count('remote_abs_path', used)))

        code.label = self._get_and_count('label', used)
        code.description = self._get_and_count('description', used)
        code.set_input_plugin_name(self._get_and_count('input_plugin', used).name)
        code.set_prepend_text(self._get_and_count('prepend_text', used))
        code.set_append_text(self._get_and_count('append_text', used))

        # Complain if there are keys that are passed but not used
        if passed_keys - used:
            raise self.CodeValidationError('Unknown parameters passed to the CodeBuilder: {}'.format(", ".join(
                sorted(passed_keys - used))))

        return code

    @staticmethod
    def from_code(code):
        """Create CodeBuilder from existing code instance.

        See also :py:func:`~CodeBuilder.get_code_spec`
        """
        spec = CodeBuilder.get_code_spec(code)
        return CodeBuilder(**spec)

    @staticmethod
    def get_code_spec(code):
        """Get code attributes from existing code instance.

        These attributes can be used to create a new CodeBuilder::

            spec = CodeBuilder.get_code_spec(old_code)
            builder = CodeBuilder(**spec)
            new_code = builder.new()

        """
        spec = {}
        spec['label'] = code.label
        spec['description'] = code.description
        spec['input_plugin'] = code.get_input_plugin_name()
        spec['prepend_text'] = code.get_prepend_text()
        spec['append_text'] = code.get_append_text()

        if code.is_local():
            spec['code_type'] = CodeBuilder.CodeType.STORE_AND_UPLOAD
            spec['code_folder'] = code.get_code_folder()
            spec['code_rel_path'] = code.get_code_rel_path()
        else:
            spec['code_type'] = CodeBuilder.CodeType.ON_COMPUTER
            spec['computer'] = code.get_remote_computer()
            spec['remote_abs_path'] = code.get_remote_exec_path()

        return spec

    def __getattr__(self, key):
        """Access code attributes used to build the code"""
        if not key.startswith('_'):
            try:
                return self._code_spec[key]
            except KeyError:
                raise KeyError("Attribute '{}' not set".format(key))
        return None

    def _get(self, key):
        """
        Return a spec, or None if not defined

        :param key: name of a code spec
        """
        return self._code_spec.get(key)

    def _get_and_count(self, key, used):
        """
        Return a spec, or raise if not defined.
        Moreover, add the key to the 'used' dict.

        :param key: name of a code spec
        :param used: should be a set of keys that you want to track.
           ``key`` will be added to this set if the value exists in the spec and can be retrieved.
        """
        retval = self.__getattr__(key)
        # I first get a retval, so if I get an exception, I don't add it to the 'used' set
        used.add(key)
        return retval

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            self._set_code_attr(key, value)
        super(CodeBuilder, self).__setattr__(key, value)

    def _set_code_attr(self, key, value):
        """Set a code attribute, if it passes validation.

        Checks compatibility with other code attributes.
        """
        # store only string of input plugin
        if key == 'input_plugin' and isinstance(value, PluginParamType):
            value = value.name

        backup = self._code_spec.copy()
        self._code_spec[key] = value
        success, _ = self.validate(raise_error=False)
        if not success:
            self._code_spec = backup
            self.validate()

    def validate_code_type(self):
        """Make sure the code type is set correctly"""
        if self._get('code_type') and self.code_type not in self.CodeType:
            raise self.CodeValidationError('invalid code type: must be one of {}, not {}'.format(
                list(self.CodeType), self.code_type))

    def validate_upload(self):
        """If the code is stored and uploaded, catch invalid on-computer attributes"""
        messages = []
        if self.is_local():
            if self._get('computer'):
                messages.append('invalid option for store-and-upload code: "computer"')
            if self._get('remote_abs_path'):
                messages.append('invalid option for store-and-upload code: "remote_abs_path"')
        if messages:
            raise self.CodeValidationError('{}'.format(messages))

    def validate_installed(self):
        """If the code is on-computer, catch invalid store-and-upload attributes"""
        messages = []
        if self._get('code_type') == self.CodeType.ON_COMPUTER:
            if self._get('code_folder'):
                messages.append('invalid options for on-computer code: "code_folder"')
            if self._get('code_rel_path'):
                messages.append('invalid options for on-computer code: "code_rel_path"')
        if messages:
            raise self.CodeValidationError('{}'.format(messages))

    class CodeValidationError(Exception):
        """
        A CodeBuilder instance may raise this

         * when asked to instanciate a code with missing or invalid code attributes
         * when asked for a code attibute that has not been set yet
        """

        def __init__(self, msg):
            super(CodeBuilder.CodeValidationError, self).__init__()
            self.msg = msg

        def __str__(self):
            return self.msg

        def __repr__(self):
            return '<CodeValidationError: {}>'.format(self)

    def is_local(self):
        """Analogous to Code.is_local()"""
        return self.__getattr__('code_type') == self.CodeType.STORE_AND_UPLOAD

    # pylint: disable=too-few-public-methods
    class CodeType(enum.Enum):
        STORE_AND_UPLOAD = 'store in the db and upload'
        ON_COMPUTER = 'on computer'

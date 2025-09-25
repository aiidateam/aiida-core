###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Manage code objects with lazy loading of the db env"""

import enum
import pathlib

from aiida.common.utils import ErrorAccumulator
from aiida.common.warnings import warn_deprecation
from aiida.orm import InstalledCode, PortableCode


class CodeBuilder:
    """Build a code with validation of attribute combinations"""

    def __init__(self, **kwargs):
        """Construct a new instance."""
        warn_deprecation(
            'CodeBuilder is deprecated. To create a new code instance, use its constructor.',
            version=3,
        )
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

    def new(self):
        """Build and return a new code instance (not stored)"""
        from aiida.manage import get_manager

        # Load the profile backend if not already the case.
        get_manager().get_profile_storage()

        self.validate()

        # Will be used at the end to check if all keys are known (those that are not None)
        passed_keys = set(k for k in self._code_spec.keys() if self._code_spec[k] is not None)
        used = set()

        if self._get_and_count('code_type', used) == self.CodeType.STORE_AND_UPLOAD:
            code = PortableCode(
                filepath_executable=self._get_and_count('code_rel_path', used),
                filepath_files=pathlib.Path(self._get_and_count('code_folder', used)),
            )
        else:
            code = InstalledCode(
                computer=self._get_and_count('computer', used),
                filepath_executable=self._get_and_count('remote_abs_path', used),
            )

        code.label = self._get_and_count('label', used)
        code.description = self._get_and_count('description', used)
        code.default_calc_job_plugin = self._get_and_count('input_plugin', used)
        code.use_double_quotes = self._get_and_count('use_double_quotes', used)
        code.prepend_text = self._get_and_count('prepend_text', used)
        code.append_text = self._get_and_count('append_text', used)

        # Complain if there are keys that are passed but not used
        if passed_keys - used:
            raise self.CodeValidationError(
                f"Unknown parameters passed to the CodeBuilder: {', '.join(sorted(passed_keys - used))}"
            )

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
        spec['input_plugin'] = code.default_calc_job_plugin
        spec['use_double_quotes'] = code.use_double_quotes
        spec['prepend_text'] = code.prepend_text
        spec['append_text'] = code.append_text

        if isinstance(code, PortableCode):
            spec['code_type'] = CodeBuilder.CodeType.STORE_AND_UPLOAD
            spec['code_folder'] = code.get_code_folder()
            spec['code_rel_path'] = code.get_code_rel_path()
        else:
            spec['code_type'] = CodeBuilder.CodeType.ON_COMPUTER
            spec['computer'] = code.computer
            spec['remote_abs_path'] = str(code.get_executable())

        return spec

    def __getattr__(self, key):
        """Access code attributes used to build the code"""
        if not key.startswith('_'):
            try:
                return self._code_spec[key]
            except KeyError:
                raise KeyError(f"Attribute '{key}' not set")
        return None

    def _get(self, key):
        """Return a spec, or None if not defined

        :param key: name of a code spec
        """
        return self._code_spec.get(key)

    def _get_and_count(self, key, used):
        """Return a spec, or raise if not defined.
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
        super().__setattr__(key, value)

    def _set_code_attr(self, key, value):
        """Set a code attribute, if it passes validation.

        Checks compatibility with other code attributes.
        """
        if key == 'description' and value is None:
            value = ''

        backup = self._code_spec.copy()
        self._code_spec[key] = value
        success, _ = self.validate(raise_error=False)
        if not success:
            self._code_spec = backup
            self.validate()

    def validate_code_type(self):
        """Make sure the code type is set correctly"""
        if self._get('code_type') and self.code_type not in self.CodeType:
            raise self.CodeValidationError(
                f'invalid code type: must be one of {list(self.CodeType)}, not {self.code_type}'
            )

    def validate_upload(self):
        """If the code is stored and uploaded, catch invalid on-computer attributes"""
        messages = []
        if self.is_local():
            if self._get('computer'):
                messages.append('invalid option for store-and-upload code: "computer"')
            if self._get('remote_abs_path'):
                messages.append('invalid option for store-and-upload code: "remote_abs_path"')
        if messages:
            raise self.CodeValidationError(f'{messages}')

    def validate_installed(self):
        """If the code is on-computer, catch invalid store-and-upload attributes"""
        messages = []
        if self._get('code_type') == self.CodeType.ON_COMPUTER:
            if self._get('code_folder'):
                messages.append('invalid options for on-computer code: "code_folder"')
            if self._get('code_rel_path'):
                messages.append('invalid options for on-computer code: "code_rel_path"')
        if messages:
            raise self.CodeValidationError(f'{messages}')

    class CodeValidationError(ValueError):
        """A CodeBuilder instance may raise this

        * when asked to instanciate a code with missing or invalid code attributes
        * when asked for a code attibute that has not been set yet
        """

        def __init__(self, msg):
            super().__init__()
            self.msg = msg

        def __str__(self):
            return self.msg

        def __repr__(self):
            return f'<CodeValidationError: {self}>'

    def is_local(self):
        """Analogous to Code.is_local()"""
        return self.__getattr__('code_type') == self.CodeType.STORE_AND_UPLOAD

    class CodeType(enum.Enum):
        STORE_AND_UPLOAD = 'store in the db and upload'
        ON_COMPUTER = 'on computer'

"""Manage code objects with lazy loading of the db env"""
import enum
import os

from aiida.cmdline.utils.decorators import with_dbenv


class ErrorAccumulator(object):
    """
    Allows to run a number of functions and collect all the errors they raise

    This allows to validate multiple things and tell the user about all the
    errors encountered at once. Works best if the individual functions do not depend on each other.

    Does not allow to trace the stack of each error, therefore do not use for debugging, but for
    semantical checking with user friendly error messages.
    """

    def __init__(self, *error_cls):
        self.error_cls = error_cls
        self.errors = {k: [] for k in self.error_cls}

    def run(self, function, *args, **kwargs):
        try:
            function(*args, **kwargs)
        except self.error_cls as err:
            self.errors[err.__class__].append(err)

    def success(self):
        return bool(not any(self.errors.values()))

    def result(self, raise_error=Exception):
        if raise_error:
            self.raise_errors(raise_error)
        return self.success(), self.errors

    def raise_errors(self, raise_cls):
        if not self.success():
            raise raise_cls('The following errors were encountered: {}'.format(self.errors))


class CodeBuilder(object):
    """Build a code with validation of attribute combinations"""

    def __init__(self, **kwargs):
        self._code_spec = kwargs
        self._validators = []
        self._err_acc = ErrorAccumulator(self.CodeValidationError)

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

        if self.code_type == self.CodeType.STORE_AND_UPLOAD:
            file_list = [os.path.realpath(os.path.join(self.code_folder, f)) for f in os.listdir(self.code_folder)]
            code = Code(local_executable=self.code_rel_path, files=file_list)
        else:
            code = Code(remote_computer_exec=(self.computer, self.remote_abs_path))

        code.label = self.label
        code.description = self.description
        code.set_input_plugin_name(self.input_plugin.name)
        code.set_prepend_text(self.prepend_text)
        code.set_append_text(self.append_text)

        return code

    def __getattr__(self, key):
        """Access code attributes used to build the code"""
        if not key.startswith('_'):
            try:
                return self._code_spec[key]
            except KeyError:
                raise self.CodeValidationError(key + ' not set')
        return None

    def _get(self, key):
        return self._code_spec.get(key)

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            self._set_code_attr(key, value)
        super(CodeBuilder, self).__setattr__(key, value)

    def _set_code_attr(self, key, value):
        """Set a code attribute if it passes validation."""
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
        if self._get('code_type') == self.CodeType.STORE_AND_UPLOAD:
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

    # pylint: disable=too-few-public-methods
    class CodeType(enum.Enum):
        STORE_AND_UPLOAD = 'store in the db and upload'
        ON_COMPUTER = 'on computer'

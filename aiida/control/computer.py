"""Manage computer objects with lazy loading of the db env"""
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from aiida.utils.error_accumulator import ErrorAccumulator


def configure_computer(computer, user=None, **kwargs):
    """Configure a computer for a user with valid auth params passed via kwargs."""
    from aiida.orm.backend import construct_backend

    transport_cls = computer.get_transport_class()
    backend = construct_backend()
    user = user or backend.users.get_automatic_user()

    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        authinfo = backend.authinfos.create(computer, user)

    auth_params = authinfo.get_auth_params()
    valid_keys = set(transport_cls.get_valid_auth_params())

    if not set(kwargs.keys()).issubset(valid_keys):
        invalid_keys = [key for key in kwargs if key not in valid_keys]
        raise ValueError('{transport}: recieved invalid authentication parameter(s) "{invalid}"'.format(
            transport=transport_cls, invalid=invalid_keys))

    if valid_keys:
        auth_params.update(kwargs)
        authinfo.set_auth_params(auth_params)
        from aiida.settings import BACKEND
        if BACKEND == 'sqlalchemy':
            authinfo._dbauthinfo.auth_params = auth_params  # pylint: disable=protected-access
    authinfo.store()


def get_computer_configuration(computer, user=None):
    """Get the configuratio of computer for user as a dictionary."""
    from aiida.orm.backend import construct_backend

    backend = construct_backend()
    user = user or backend.users.get_automatic_user()

    config = {}
    try:
        authinfo = backend.authinfos.get(computer, user)
        config = authinfo.get_auth_params()
    except NotExistent:
        pass
    return config


class ComputerBuilder(object):
    """Build a computer with validation of attribute combinations"""

    def __init__(self, **kwargs):
        self._computer_spec = {}
        self._err_acc = ErrorAccumulator(self.ComputerValidationError)

        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def validate(self, raise_error=True):
        """
        Validate the computer options
        """
        #self._err_acc.run(self.validate_installed)
        return self._err_acc.result(raise_error=self.ComputerValidationError if raise_error else False)

    @with_dbenv()
    def new(self):
        """Build and return a new computer instance (not stored)"""
        from aiida.orm import Computer

        self.validate()

        # Will be used at the end to check if all keys are known
        passed_keys = set(self._computer_spec.keys())
        used = set()

        computer = Computer()

        computer.set_name(self._get_and_count('label', used))
        computer.set_description(self._get_and_count('description', used))
        computer.set_enabled_state(self._get_and_count('enabled', used))
        computer.set_hostname(self._get_and_count('hostname', used))
        computer.set_scheduler_type(self._get_and_count('scheduler', used))
        computer.set_transport_type(self._get_and_count('transport', used))
        computer.set_prepend_text(self._get_and_count('prepend_text', used))
        computer.set_append_text(self._get_and_count('append_text', used))
        computer.set_workdir(self._get_and_count('work_dir', used))
        mpiprocs_per_machine = self._get_and_count('mpiprocs_per_machine', used)
        # In the command line, 0 means unspecified
        if mpiprocs_per_machine == 0:
            mpiprocs_per_machine = None
        if mpiprocs_per_machine is not None:
            try:
                mpiprocs_per_machine = int(mpiprocs_per_machine)
            except ValueError:
                raise self.ComputerValidationError("Invalid value provided for mpiprocs_per_machine, "
                                                   "must be a valid integer")
            if mpiprocs_per_machine <= 0:
                raise self.ComputerValidationError("Invalid value provided for mpiprocs_per_machine, "
                                                   "must be positive")
            computer.set_default_mpiprocs_per_machine(mpiprocs_per_machine)

        mpirun_command_internal = self._get_and_count('mpirun_command', used).strip().split(" ")
        if mpirun_command_internal == ['']:
            mpirun_command_internal = []
        computer._mpirun_command_validator(mpirun_command_internal)  # pylint: disable=protected-access
        computer.set_mpirun_command(mpirun_command_internal)

        computer.set_shebang(self._get_and_count('shebang', used))

        # Complain if there are keys that are passed but not used
        if passed_keys - used:
            raise self.ComputerValidationError('Unknown parameters passed to the ComputerBuilder: {}'.format(
                ", ".join(sorted(passed_keys - used))))

        return computer

    def __getattr__(self, key):
        """Access computer attributes used to build the computer"""
        if not key.startswith('_'):
            try:
                return self._computer_spec[key]
            except KeyError:
                raise self.ComputerValidationError(key + ' not set')
        return None

    def _get(self, key):
        """
        Return a spec, or None if not defined

        :param key: name of a computer spec
        """
        return self._computer_spec.get(key)

    def _get_and_count(self, key, used):
        """
        Return a spec, or raise if not defined.
        Moreover, add the key to the 'used' dict.

        :param key: name of a computer spec
        :param used: should be a set of keys that you want to track.
           ``key`` will be added to this set if the value exists in the spec and can be retrieved.
        """
        retval = self.__getattr__(key)
        ## I first get a retval, so if I get an exception, I don't add it to the 'used' set
        used.add(key)
        return retval

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            self._set_computer_attr(key, value)
        super(ComputerBuilder, self).__setattr__(key, value)

    def _set_computer_attr(self, key, value):
        """Set a computer attribute if it passes validation."""
        backup = self._computer_spec.copy()
        self._computer_spec[key] = value
        success, _ = self.validate(raise_error=False)
        if not success:
            self._computer_spec = backup
            self.validate()

    class ComputerValidationError(Exception):
        """
        A ComputerBuilder instance may raise this

         * when asked to instanciate a code with missing or invalid computer attributes
         * when asked for a computer attibute that has not been set yet
        """

        def __init__(self, msg):
            super(ComputerBuilder.ComputerValidationError, self).__init__()
            self.msg = msg

        def __str__(self):
            return self.msg

        def __repr__(self):
            return '<ComputerValidationError: {}>'.format(self)

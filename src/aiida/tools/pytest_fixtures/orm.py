"""Fixtures that provides ORM instances."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

if t.TYPE_CHECKING:
    from aiida.orm import Computer


@pytest.fixture(scope='session')
def ssh_key(tmp_path_factory) -> t.Generator[pathlib.Path, None, None]:
    """Generate a temporary SSH key pair for the test session and return the filepath of the private key.

    The filepath of the public key is the same as the private key, but it adds the ``.pub`` file extension.

    :returns: The filepath of the generated private key.
    """
    from uuid import uuid4

    from cryptography.hazmat.backends import default_backend as crypto_default_backend
    from cryptography.hazmat.primitives import serialization as crypto_serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048,
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH,
    )

    dirpath = tmp_path_factory.mktemp('keys')
    filename = uuid4().hex
    filepath_private_key = dirpath / filename
    filepath_public_key = dirpath / f'{filename}.pub'

    filepath_private_key.write_bytes(private_key)
    filepath_public_key.write_bytes(public_key)

    try:
        yield filepath_private_key
    finally:
        filepath_private_key.unlink(missing_ok=True)
        filepath_public_key.unlink(missing_ok=True)


@pytest.fixture
def aiida_computer(tmp_path) -> t.Callable[[], 'Computer']:
    """Return a factory to create a new or load an existing :class:`aiida.orm.computers.Computer` instance.

    The database is queried for an existing computer with the same ``label``, ``hostname``, ``scheduler_type`` and
    ``transport_type``. If it exists, it means it was probably created by this fixture in a previous call and it is
    simply returned. Otherwise a new instance is created. Note that the computer is not explicitly configured, unless
    ``configure_kwargs`` are specified. By default the ``localhost`` hostname is used with the ``core.direct`` and
    ``core.local`` scheduler and transport plugins.

    The factory has the following signature:

    :param label: The computer label. If not specified, a random UUID4 is used.
    :param hostname: The hostname of the computer. Defaults to ``localhost``.
    :param scheduler_type: The scheduler plugin to use. Defaults to ``core.direct``.
    :param transport_type: The transport plugin to use. Defaults to ``core.local``.
    :param minimum_job_poll_interval: The default minimum job poll interval to set. Defaults to 0.
    :param default_mpiprocs_per_machine: The default number of MPI procs to set. Defaults to 1.
    :param configuration_kwargs: Optional keyword arguments that, if defined, are used to configure the computer
        by calling :meth:`aiida.orm.computers.Computer.configure`.
    :return: A stored computer instance.
    """

    def factory(
        label: str | None = None,
        hostname='localhost',
        scheduler_type='core.direct',
        transport_type='core.local',
        minimum_job_poll_interval: int = 0,
        default_mpiprocs_per_machine: int = 1,
        configuration_kwargs: dict[t.Any, t.Any] | None = None,
    ) -> 'Computer':
        import uuid

        from aiida.common.exceptions import NotExistent
        from aiida.orm import Computer

        label = label or f'test-computer-{uuid.uuid4().hex}'

        try:
            computer = Computer.collection.get(
                label=label, hostname=hostname, scheduler_type=scheduler_type, transport_type=transport_type
            )
        except NotExistent:
            computer = Computer(
                label=label,
                hostname=hostname,
                workdir=str(tmp_path),
                transport_type=transport_type,
                scheduler_type=scheduler_type,
            )
            computer.store()
            computer.set_minimum_job_poll_interval(minimum_job_poll_interval)
            computer.set_default_mpiprocs_per_machine(default_mpiprocs_per_machine)

        if configuration_kwargs:
            computer.configure(**configuration_kwargs)

        return computer

    return factory


@pytest.fixture
def aiida_computer_local(aiida_computer) -> t.Callable[[], Computer]:
    """Factory to return a :class:`aiida.orm.computers.Computer` instance with ``core.local`` transport.

    Usage::

        def test(aiida_computer_ssh):
            computer = aiida_computer_ssh(label='some-label', configure=True)
            assert computer.transport_type == 'core.local'
            assert computer.is_configured

    The factory has the following signature:

    :param label: The computer label. If not specified, a random UUID4 is used.
    :param configure: Boolean, if ``True``, ensures the computer is configured, otherwise the computer is returned
        as is. Note that if a computer with the given label already exists and it was configured before, the
        computer will not be "un-"configured. If an unconfigured computer is absolutely required, make sure to first
        delete the existing computer or specify another label.
    :return: A stored computer instance.
    """

    def factory(label: str | None = None, configure: bool = True) -> Computer:
        computer = aiida_computer(label=label, hostname='localhost', transport_type='core.local')

        if configure:
            computer.configure()

        return computer

    return factory


@pytest.fixture
def aiida_computer_ssh(aiida_computer, ssh_key) -> t.Callable[[], 'Computer']:
    """Factory to return a :class:`aiida.orm.computers.Computer` instance with ``core.ssh`` transport.

    If ``configure=True``, an SSH key pair is automatically added to the ``.ssh`` folder of the user, allowing an
    actual SSH connection to be made to the localhost.

    Usage::

        def test(aiida_computer_ssh):
            computer = aiida_computer_ssh(label='some-label', configure=True)
            assert computer.transport_type == 'core.ssh'
            assert computer.is_configured

    The factory has the following signature:

    :param label: The computer label. If not specified, a random UUID4 is used.
    :param configure: Boolean, if ``True``, ensures the computer is configured, otherwise the computer is returned
        as is. Note that if a computer with the given label already exists and it was configured before, the
        computer will not be "un-"configured. If an unconfigured computer is absolutely required, make sure to first
        delete the existing computer or specify another label.
    :return: A stored computer instance.
    """

    def factory(label: str | None = None, configure: bool = True) -> 'Computer':
        computer = aiida_computer(label=label, hostname='localhost', transport_type='core.ssh')

        if configure:
            computer.configure(
                key_filename=str(ssh_key),
                key_policy='AutoAddPolicy',
                safe_interval=1.0,
            )

        return computer

    return factory


@pytest.fixture
def aiida_computer_ssh_async(aiida_computer) -> t.Callable[[], 'Computer']:
    """Factory to return a :class:`aiida.orm.computers.Computer` instance with ``core.ssh_async`` transport.

    Usage::

        def test(aiida_computer_ssh):
            computer = aiida_computer_ssh(label='some-label', configure=True)
            assert computer.transport_type == 'core.ssh_async'
            assert computer.is_configured

    The factory has the following signature:

    :param label: The computer label. If not specified, a random UUID4 is used.
    :param configure: Boolean, if ``True``, ensures the computer is configured, otherwise the computer is returned
        as is. Note that if a computer with the given label already exists and it was configured before, the
        computer will not be "un-"configured. If an unconfigured computer is absolutely required, make sure to first
        delete the existing computer or specify another label.
    :return: A stored computer instance.
    """

    def factory(label: str | None = None, configure: bool = True, backend: str | None = None) -> 'Computer':
        """
        Create or load a computer with the ``core.ssh_async`` transport.
        :param label: The computer label. If not specified, a random UUID4 is used.
        :param configure: Boolean, if ``True``, ensures the computer is configured.
        :param backend: The backend to use for the async SSH transport. it can be either `asyncssh` or `openssh`
            If not specified, it raises a ValueError.
        """

        def if_exists_and_is_configured(label):
            from aiida.common.exceptions import NotExistent
            from aiida.orm.utils import load_computer

            try:
                computer = load_computer(label=label)
                if computer.is_configured:
                    return True
            except NotExistent:
                pass
            return False

        if configure and backend is None and not if_exists_and_is_configured(label):
            # For accurate testing, we don't set a default value for this.
            # It should be explicitly specified to error nasty bugs.
            raise ValueError(
                'The `backend` argument must be specified when configuring a computer with `core.ssh_async` transport.'
            )
        computer = aiida_computer(label=label, hostname='localhost', transport_type='core.ssh_async')
        if configure:
            computer.configure(backend=backend)

        return computer

    return factory


@pytest.fixture
def aiida_localhost(aiida_computer_local) -> 'Computer':
    """Return a :class:`aiida.orm.computers.Computer` instance representing localhost with ``core.local`` transport.

    Usage::

        def test(aiida_localhost):
            assert aiida_localhost.transport_type == 'core.local'

    :return: The computer.
    """
    return aiida_computer_local(label='localhost')


@pytest.fixture
def aiida_code():
    """Return a factory to create a new or load an existing :class:`aiida.orm.nodes.data.code.abstract.AbstractCode`.

    Usage::

        def test(aiida_localhost, aiida_code):
            from aiida.orm import InstalledCode
            code = aiida_code(
                'core.code.installed',
                label='test-code',
                computer=aiida_localhost,
                filepath_executable='/bin/bash'
            )
            assert isinstance(code, InstalledCode)

    The factory has the following signature:

    :param entry_point: Entry point of the code plugin.
    :param label: The label of the code. Default to a randomly generated string.
    :param kwargs: Additional keyword arguments that are passed to the code's constructor.
    :return: The created or loaded code instance.
    """

    def factory(entry_point: str, label: str | None = None, **kwargs):
        import uuid

        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm import QueryBuilder
        from aiida.plugins import DataFactory

        cls = DataFactory(entry_point)
        label = label or f'test-code-{uuid.uuid4().hex}'

        try:
            code = QueryBuilder().append(cls, filters={'label': label}).one()[0]
        except (MultipleObjectsError, NotExistent):
            code = cls(label=label, **kwargs).store()

        return code

    return factory


@pytest.fixture
def aiida_code_installed(aiida_code, aiida_localhost):
    """Return a factory to create a new or load an existing :class:`aiida.orm.nodes.data.code.installed.InstalledCode`.

    Usage::

        def test(aiida_code_installed):
            from aiida.orm import InstalledCode
            code = aiida_code_installed()
            assert isinstance(code, InstalledCode)

    The factory has the following signature:

    :param label: The label of the code. Default to a randomly generated string.
    :param default_calc_job_plugin: Optional default calcjob plugin to set.
    :param computer: The computer to set. Defaults to localhost computer of the ``aiida_localhost`` fixture.
    :param filepath_executable: The filepath of the executable. Defaults to ``/bin/bash``.
    :param use_double_quotes: Whether the executable and arguments of the code in the submission script should be
        escaped with single or double quotes.
    :param with_mpi: Whether the executable should be run as an MPI program.
    :param prepend_text: Optional bash commands that should be executed in the submission script before the executable.
    :param append_text: Optional bash commands that should be executed in the submission script after the executable.
    :return: The created or loaded code instance.
    """

    def factory(
        label: str | None = None,
        description: str | None = None,
        default_calc_job_plugin: str | None = None,
        computer: Computer = aiida_localhost,
        filepath_executable: str = '/bin/bash',
        use_double_quotes: bool = False,
        with_mpi: bool | None = None,
        prepend_text: str = '',
        append_text: str = '',
    ):
        return aiida_code(
            'core.code.installed',
            label=label,
            description=description,
            default_calc_job_plugin=default_calc_job_plugin,
            computer=computer,
            filepath_executable=filepath_executable,
            use_double_quotes=use_double_quotes,
            with_mpi=with_mpi,
            prepend_text=prepend_text,
            append_text=append_text,
        )

    return factory

import json
from pathlib import Path

import pytest

TARGETS = ('aiida-core-base', 'aiida-core-with-services', 'aiida-core-dev')


def target_checker(value):
    msg = f"Invalid image target '{value}', must be one of: {TARGETS}"
    if value not in TARGETS:
        raise pytest.UsageError(msg)
    return value


def pytest_addoption(parser):
    parser.addoption(
        '--variant',
        action='store',
        required=True,
        help='target (image name) of the docker-compose file to use.',
        type=target_checker,
    )


@pytest.fixture(scope='session')
def variant(pytestconfig):
    return pytestconfig.getoption('variant')


@pytest.fixture(scope='session')
def docker_compose_file(variant):
    return f'docker-compose.{variant}.yml'


@pytest.fixture(scope='session')
def docker_compose(docker_services):
    return docker_services._docker_compose


@pytest.fixture(scope='session', autouse=True)
def _docker_service_wait(docker_services):
    """Container startup wait."""

    # using `docker_compose` fixture would
    # trigger a separate container
    docker_compose = docker_services._docker_compose

    def is_container_ready():
        try:
            output = docker_compose.execute('exec -T aiida verdi status').decode().strip()
            print('OUTPUT', output)
        except Exception:
            return False
        return '✔ broker:' in output and 'Daemon is running' in output

    docker_services.wait_until_responsive(
        timeout=600.0,
        pause=2,
        check=lambda: is_container_ready(),
    )


@pytest.fixture
def container_user():
    return 'aiida'


@pytest.fixture
def aiida_exec(docker_compose):
    def execute(command, user=None, **kwargs):
        if user:
            command = f'exec -T --user={user} aiida {command}'
        else:
            command = f'exec -T aiida {command}'
        return docker_compose.execute(command, **kwargs)

    return execute


@pytest.fixture(scope='session')
def _build_config():
    return json.loads(Path('build.json').read_text(encoding='utf-8'))['variable']


@pytest.fixture(scope='session')
def python_version(_build_config):
    return _build_config['PYTHON_VERSION']['default']


@pytest.fixture(scope='session')
def pgsql_version(_build_config):
    return _build_config['PGSQL_VERSION']['default']


@pytest.fixture(scope='session')
def rmq_version(_build_config):
    return _build_config['RMQ_VERSION']['default']

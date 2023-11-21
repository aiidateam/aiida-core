# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, redefined-outer-name
import json
from pathlib import Path

import pytest


@pytest.fixture(scope='session', params=['aiida-core-base', 'aiida-core-with-services'])
def variant(request):
    return request.param


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig, variant):  # pylint: disable=unused-argument
    return f'docker-compose.{variant}.yml'


@pytest.fixture(scope='session')
def docker_compose(docker_services):
    # pylint: disable=protected-access
    return docker_services._docker_compose


def is_container_ready(docker_compose):
    output = docker_compose.execute('exec -T aiida verdi status').decode().strip()
    return 'Connected to RabbitMQ' in output and 'Daemon is running' in output


@pytest.fixture(scope='session', autouse=True)
def _docker_service_wait(docker_services):
    """Container startup wait."""
    docker_compose = docker_services._docker_compose

    docker_services.wait_until_responsive(timeout=120.0, pause=0.1, check=lambda: is_container_ready(docker_compose))


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

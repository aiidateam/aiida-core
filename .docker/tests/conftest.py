# -*- coding: utf-8 -*-
import json
from pathlib import Path

import pytest


@pytest.fixture(scope='session', params=['base', 'base-with-services'])
def variant(request):
    return request.param


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig, variant):
    return f'docker-compose.{variant}.yml'


@pytest.fixture(scope='session')
def docker_compose(docker_services):
    return docker_services._docker_compose


@pytest.fixture
def timeout():
    """Container and service startup timeout"""
    return 30


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
    return json.loads(Path('build.json').read_text())['variable']


@pytest.fixture(scope='session')
def python_version(_build_config):
    return _build_config['PYTHON_VERSION']['default']


@pytest.fixture(scope='session')
def pgsql_version(_build_config):
    return _build_config['PGSQL_VERSION']['default']

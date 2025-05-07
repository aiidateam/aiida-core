import json
import re

import pytest
from packaging.version import parse


def test_correct_python_version_installed(aiida_exec, python_version):
    info = json.loads(aiida_exec('mamba list --json --full-name python', ignore_stderr=True).decode())[0]
    assert info['name'] == 'python'
    assert parse(info['version']) == parse(python_version)


def test_correct_pgsql_version_installed(aiida_exec, pgsql_version, variant):
    if variant == 'aiida-core-base':
        pytest.skip('PostgreSQL is not installed in the base image')

    info = json.loads(aiida_exec('mamba list --json --full-name postgresql', ignore_stderr=True).decode())[0]
    assert info['name'] == 'postgresql'
    assert parse(info['version']).major == parse(pgsql_version).major


def test_rmq_consumer_timeout_unset(aiida_exec, variant):
    if variant == 'aiida-core-base':
        pytest.skip('RabbitMQ is not installed in the base image')

    output = aiida_exec('rabbitmqctl environment | grep consumer_timeout', user='root').decode().strip()
    assert 'undefined' in output


def test_verdi_status(aiida_exec, container_user):
    output = aiida_exec('verdi status', user=container_user).decode().strip()
    assert '✔ broker:' in output
    assert 'Daemon is running' in output

    # Check that we have suppressed the warnings coming from using an install from repo and newer RabbitMQ version.
    # Make sure to match only lines that start with ``Warning:`` because otherwise deprecation warnings from other
    # packages that we cannot control may fail the test.
    assert not re.match('^Warning:.*', output)


def test_computer_setup_success(aiida_exec, container_user):
    output = aiida_exec('verdi computer test localhost', user=container_user).decode().strip()

    assert 'Success' in output
    assert 'Failed' not in output


def test_clone_dir_exists(aiida_exec, variant):
    """Test that the aiida-core repository is cloned in the aiida-core-dev image."""
    if variant != 'aiida-core-dev':
        pytest.skip(f'aiida-core clone not available in {variant} image')

    output = aiida_exec('ls /home/aiida/').decode().strip()

    assert 'aiida-core' in output


def test_editable_install(aiida_exec, variant):
    """Test that the aiida-core repository is installed in editable mode in the aiida-core-dev image."""
    if variant != 'aiida-core-dev':
        pytest.skip(f'aiida-core clone not available in {variant} image')

    package = 'aiida-core'

    output = aiida_exec(f'pip show {package}').decode().strip()

    assert f'Editable project location: /home/aiida/{package}' in output


@pytest.mark.parametrize(
    'package',
    [
        'ase',
        'Sphinx',
        'pre-commit',
        'Flask',
        'pytest',
        'trogon',
    ],
)
def test_optional_dependency_install(aiida_exec, package, variant):
    """Test that optional dependencies are installed in the aiida-core-dev image."""
    if variant != 'aiida-core-dev':
        pytest.skip(f'optional dependencies are not installed in {variant} image')

    output = aiida_exec(f'pip show {package}').decode().strip()

    assert f'Name: {package}' in output

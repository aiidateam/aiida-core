import json

import pytest
from packaging.version import parse


def test_correct_python_version_installed(aiida_exec, python_version):
    info = json.loads(aiida_exec('mamba list --json --full-name python').decode())[0]
    assert info['name'] == 'python'
    assert parse(info['version']) == parse(python_version)


def test_correct_pgsql_version_installed(aiida_exec, pgsql_version, variant):
    if variant == 'aiida-core-base':
        pytest.skip('PostgreSQL is not installed in the base image')

    info = json.loads(aiida_exec('mamba list --json --full-name postgresql').decode())[0]
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

    # check that we have suppressed the warnings
    assert 'Warning' not in output


def test_computer_setup_success(aiida_exec, container_user):
    output = aiida_exec('verdi computer test localhost', user=container_user).decode().strip()

    assert 'Success' in output
    assert 'Failed' not in output

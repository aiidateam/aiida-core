###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi notebook``."""

import json
import sys

from aiida.cmdline.commands import cmd_notebook, cmd_status
from aiida.manage.configuration import get_config


def test_notebook_install(run_cli_command, tmp_path, monkeypatch):
    """Test ``verdi notebook install``.

    What the kernel specification has to carry is the interpreter and the configuration directory, since the
    Jupyter server starts a kernel without either of them.
    """
    monkeypatch.setenv('JUPYTER_DATA_DIR', str(tmp_path))

    result = run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'])
    filepath = tmp_path / 'kernels' / 'aiida-test' / 'kernel.json'

    assert str(filepath.parent) in result.output, result.output

    spec = json.loads(filepath.read_text(encoding='utf-8'))

    assert spec['argv'][0] == sys.executable
    assert spec['env']['AIIDA_PATH'] == str(get_config().dirpath)


def test_status_reports_registered_kernel(run_cli_command, tmp_path, monkeypatch):
    """Test `verdi status` reports the kernel registered for the configuration."""
    monkeypatch.setenv('JUPYTER_DATA_DIR', str(tmp_path))

    result = run_cli_command(cmd_status.verdi_status)
    assert 'no kernel registered for this configuration' in result.output

    run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'])

    result = run_cli_command(cmd_status.verdi_status)
    assert "kernel 'AiiDA (" in result.output
    assert 'no kernel registered' not in result.output


def read_spec(tmp_path):
    """Return the installed test kernel specification as a dictionary."""
    filepath = tmp_path / 'kernels' / 'aiida-test' / 'kernel.json'
    return json.loads(filepath.read_text(encoding='utf-8')), filepath


def test_notebook_install_keeps_existing_env(run_cli_command, tmp_path, monkeypatch):
    """Test reinstalling keeps hand-added variables and updates ``AIIDA_PATH``."""
    monkeypatch.setenv('JUPYTER_DATA_DIR', str(tmp_path))

    run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'])
    spec, filepath = read_spec(tmp_path)
    spec['env']['EXTRA'] = 'kept'
    spec['env']['AIIDA_PATH'] = '/somewhere/else'
    filepath.write_text(json.dumps(spec), encoding='utf-8')

    result = run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test', '--force'])
    assert 'retained variables' in result.output

    spec, _ = read_spec(tmp_path)
    assert spec['env']['EXTRA'] == 'kept'
    assert spec['env']['AIIDA_PATH'] == str(get_config().dirpath)


def test_notebook_install_up_to_date(run_cli_command, tmp_path, monkeypatch):
    """Test reinstalling an identical kernel reports it instead of prompting."""
    monkeypatch.setenv('JUPYTER_DATA_DIR', str(tmp_path))

    run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'])
    result = run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'])
    assert 'already up to date' in result.output


def test_notebook_install_prompts_on_change(run_cli_command, tmp_path, monkeypatch):
    """Test a changed configuration prompts before overwriting."""
    monkeypatch.setenv('JUPYTER_DATA_DIR', str(tmp_path))

    run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'])
    spec, filepath = read_spec(tmp_path)
    spec['env']['AIIDA_PATH'] = '/somewhere/else'
    filepath.write_text(json.dumps(spec), encoding='utf-8')

    result = run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'], user_input='n\n', raises=True)
    assert 'Aborted' in result.output
    spec, _ = read_spec(tmp_path)
    assert spec['env']['AIIDA_PATH'] == '/somewhere/else'

    result = run_cli_command(cmd_notebook.notebook_install, ['--name', 'aiida-test'], user_input='y\n')
    assert 'registered the kernel' in result.output
    spec, _ = read_spec(tmp_path)
    assert spec['env']['AIIDA_PATH'] == str(get_config().dirpath)


def test_status_without_jupyter(run_cli_command, monkeypatch):
    """Test `verdi status` stays silent on notebooks when Jupyter is not installed."""
    import builtins

    real_import = builtins.__import__

    def without_jupyter(name, *args, **kwargs):
        if name == 'jupyter_client' or name.startswith('jupyter_client.'):
            raise ImportError('no Jupyter here')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', without_jupyter)

    result = run_cli_command(cmd_status.verdi_status)
    assert 'notebook' not in result.output

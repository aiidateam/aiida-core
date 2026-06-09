###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.cmdline.utils.template_config`."""

import textwrap

import click
import pytest

from aiida.cmdline.utils.template_config import (
    _process_content,
    load_and_process_template,
    parse_template_vars,
)


def _fake_response(text, *, ok=True):
    """Build a fake ``requests.Response`` for monkeypatching ``requests.get``."""
    import requests

    class _Response:
        status_code = 200 if ok else 500

        def raise_for_status(self):
            if not ok:
                raise requests.ConnectionError(text)

    _Response.text = text
    return _Response()


class TestProcessContent:
    """Tests for :func:`_process_content` — the core processing pipeline."""

    def test_plain_yaml_passthrough(self):
        """Plain YAML without templates or metadata passes through unchanged."""
        content = 'label: my-computer\nhostname: localhost\n'
        result = _process_content(content, interactive=False)
        assert result == {'label': 'my-computer', 'hostname': 'localhost'}

    def test_metadata_stripped(self):
        """The ``metadata`` section is stripped from plain YAML."""
        content = textwrap.dedent("""\
            label: my-computer
            metadata:
                tooltip: Some tooltip
        """)
        result = _process_content(content, interactive=False)
        assert result == {'label': 'my-computer'}

    def test_template_rendering_non_interactive(self):
        """Template variables are resolved from ``template_vars`` in non-interactive mode."""
        content = textwrap.dedent("""\
            label: '{{ label }}'
            hostname: localhost
            metadata:
                template_variables:
                    label:
                        default: test-computer
                        type: text
        """)
        result = _process_content(content, interactive=False, template_vars={'label': 'my-computer'})
        assert result == {'label': 'my-computer', 'hostname': 'localhost'}

    def test_template_vars_without_metadata(self):
        """Template variables without a ``metadata`` section still render from provided vars."""
        content = "label: '{{ label }}'\nhostname: localhost\n"
        result = _process_content(content, interactive=False, template_vars={'label': 'test'})
        assert result == {'label': 'test', 'hostname': 'localhost'}

    def test_template_vars_without_metadata_warns_interactive(self, capsys):
        """In interactive mode, template variables without metadata emit a warning but don't fail."""
        content = "label: '{{ label }}'\nhostname: localhost\n"
        result = _process_content(content, interactive=True)
        assert result == {'label': '{{ label }}', 'hostname': 'localhost'}
        assert 'no metadata found' in capsys.readouterr().out

    @pytest.mark.parametrize(
        ('content', 'match'),
        [
            pytest.param(':\ninvalid: [yaml', 'Invalid YAML', id='invalid_yaml'),
            pytest.param('- item1\n- item2\n', 'Expected a YAML mapping', id='non_dict_yaml'),
            pytest.param(
                "label: '{{ label }}'\nmetadata:\n  template_variables:\n    label:\n      description: x\n",
                r'Template variables detected.*but no values provided',
                id='missing_vars_non_interactive',
            ),
        ],
    )
    def test_invalid_input_raises(self, content, match):
        with pytest.raises(click.BadParameter, match=match):
            _process_content(content, interactive=False)

    def test_registry_computer_format(self):
        """Realistic computer-setup YAML: templates render, AiiDA placeholders preserved, metadata stripped."""
        content = textwrap.dedent("""\
            label: '{{ label }}'
            hostname: eiger.cscs.ch
            transport: core.ssh
            scheduler: core.slurm
            work_dir: /scratch/{username}/aiida_run/
            mpirun_command: srun -n {tot_num_mpiprocs}
            prepend_text: |-
                #SBATCH --partition={{ slurm_partition }}
                #SBATCH --account={{ slurm_account }}
            metadata:
                tooltip: Some HTML tooltip
                template_variables:
                    label:
                        default: eiger-mc
                    slurm_partition:
                        default: normal
                    slurm_account:
                        description: The slurm account
        """)
        result = _process_content(
            content,
            interactive=False,
            template_vars={'label': 'eiger-mc', 'slurm_partition': 'normal', 'slurm_account': 'my_project'},
        )
        assert result == {
            'label': 'eiger-mc',
            'hostname': 'eiger.cscs.ch',
            'transport': 'core.ssh',
            'scheduler': 'core.slurm',
            'work_dir': '/scratch/{username}/aiida_run/',
            'mpirun_command': 'srun -n {tot_num_mpiprocs}',
            'prepend_text': '#SBATCH --partition=normal\n#SBATCH --account=my_project',
        }

    def test_registry_code_format_with_multiline_expression(self):
        """Realistic code YAML with a multi-line Jinja2 expression (``{{ }}`` spanning two lines)."""
        content = textwrap.dedent("""\
            label: '{{ code_binary_name }}-7.4'
            default_calc_job_plugin: quantumespresso.{{ code_binary_name }}
            filepath_executable: /opt/bin/{{
                code_binary_name }}.x
            prepend_text: |
                module load quantum-espresso/7.4.0
            metadata:
                template_variables:
                    code_binary_name:
                        type: list
                        options:
                            - pw
                            - ph
        """)
        result = _process_content(content, interactive=False, template_vars={'code_binary_name': 'pw'})
        assert result['label'] == 'pw-7.4'
        assert result['default_calc_job_plugin'] == 'quantumespresso.pw'
        assert result['filepath_executable'] == '/opt/bin/pw.x'
        assert 'metadata' not in result


class TestLoadAndProcessTemplate:
    """Tests for :func:`load_and_process_template` — file loading + processing."""

    def test_from_file(self, tmp_path):
        filepath = tmp_path / 'config.yaml'
        filepath.write_text('label: my-computer\nhostname: localhost\n')
        result = load_and_process_template(str(filepath), interactive=False)
        assert result == {'label': 'my-computer', 'hostname': 'localhost'}

    def test_from_url(self, monkeypatch):
        """Loading a template from a URL fetches and processes the content."""
        import requests

        monkeypatch.setattr(
            requests, 'get', lambda *a, **kw: _fake_response('label: url-computer\nhostname: remote-host\n')
        )
        result = load_and_process_template('https://example.com/config.yaml', interactive=False)
        assert result == {'label': 'url-computer', 'hostname': 'remote-host'}

    def test_file_not_found(self):
        with pytest.raises(click.BadParameter, match='Failed to read file'):
            load_and_process_template('/nonexistent/path.yaml', interactive=False)

    def test_url_failure(self, monkeypatch):
        """A failing URL request raises ``click.BadParameter``."""
        import requests

        monkeypatch.setattr(requests, 'get', lambda *a, **kw: (_ for _ in ()).throw(requests.ConnectionError('fail')))
        with pytest.raises(click.BadParameter, match='Failed to fetch URL'):
            load_and_process_template('https://example.com/config.yaml', interactive=False)


class TestParseTemplateVars:
    """Tests for :func:`parse_template_vars` — file / URL / JSON resolution chain."""

    def test_from_json_string(self):
        result = parse_template_vars('{"key": "value", "num": "42"}')
        assert result == {'key': 'value', 'num': '42'}

    def test_from_yaml_file(self, tmp_path):
        filepath = tmp_path / 'vars.yaml'
        filepath.write_text('account: my_project\npartition: normal\n')
        result = parse_template_vars(str(filepath))
        assert result == {'account': 'my_project', 'partition': 'normal'}

    def test_from_url(self, monkeypatch):
        import requests

        monkeypatch.setattr(requests, 'get', lambda *a, **kw: _fake_response('account: remote_project\n'))
        result = parse_template_vars('https://example.com/vars.yaml')
        assert result == {'account': 'remote_project'}

    @pytest.mark.parametrize(
        ('value', 'match'),
        [
            pytest.param('not valid json', 'Invalid JSON', id='invalid_json'),
            pytest.param('["a", "b"]', 'must contain a YAML/JSON mapping', id='json_array'),
            pytest.param('"just a string"', 'must contain a YAML/JSON mapping', id='json_string'),
        ],
    )
    def test_invalid_input_raises(self, value, match):
        with pytest.raises(click.BadParameter, match=match):
            parse_template_vars(value)

    @pytest.mark.parametrize(
        ('file_content', 'match'),
        [
            pytest.param(':\n  [invalid yaml', 'Invalid YAML', id='invalid_yaml'),
            pytest.param('- item1\n- item2\n', 'must contain a YAML/JSON mapping', id='non_dict_yaml'),
        ],
    )
    def test_file_with_bad_content_raises(self, tmp_path, file_content, match):
        filepath = tmp_path / 'bad.yaml'
        filepath.write_text(file_content)
        with pytest.raises(click.BadParameter, match=match):
            parse_template_vars(str(filepath))

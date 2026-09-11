###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.cmdline.utils.template_config`."""

import re
import textwrap

import click
import pytest

from aiida.cmdline.utils.template_config import (
    _load_content,
    _render_template,
    parse_template_vars,
    process_template_content,
)


class _FakeResponse:
    """Stand-in for a successful ``requests.Response``, for monkeypatching ``requests.get``."""

    status_code = 200

    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        pass


class TestProcessTemplateContent:
    """Tests for :func:`process_template_content` -- the core processing pipeline."""

    def test_plain_yaml_passthrough(self):
        """Plain YAML without templates or metadata passes through unchanged."""
        content = 'label: my-computer\nhostname: localhost\n'
        result = process_template_content(content, interactive=False)
        assert result == {'label': 'my-computer', 'hostname': 'localhost'}

    def test_metadata_stripped(self):
        """The ``metadata`` section is stripped from plain YAML."""
        content = textwrap.dedent("""\
            label: my-computer
            metadata:
                tooltip: Some tooltip
        """)
        result = process_template_content(content, interactive=False)
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
        result = process_template_content(content, interactive=False, template_vars={'label': 'my-computer'})
        assert result == {'label': 'my-computer', 'hostname': 'localhost'}

    def test_template_vars_without_metadata(self):
        """Template variables without a ``metadata`` section still render from provided vars."""
        content = "label: '{{ label }}'\nhostname: localhost\n"
        result = process_template_content(content, interactive=False, template_vars={'label': 'test'})
        assert result == {'label': 'test', 'hostname': 'localhost'}

    @pytest.mark.parametrize(
        'template_vars',
        (None, {}, {'unrelated': 'value'}),
        ids=('none', 'empty_mapping', 'unrelated_key'),
    )
    def test_unresolved_placeholders_without_metadata_raise(self, template_vars):
        """Placeholders that no ``metadata`` section describes must still be refused, never passed through verbatim.

        Returning the raw content here created entities labelled ``{{ label }}``, silently and with a zero exit code.
        """
        content = "label: '{{ label }}'\nhostname: localhost\n"
        with pytest.raises(click.BadParameter, match='No value provided for the template variables: label'):
            process_template_content(content, interactive=False, template_vars=template_vars)

    def test_partial_template_vars_are_merged_with_prompts(self, monkeypatch):
        """Values given on the command line seed the prompts rather than replacing them."""
        prompted = []

        def _prompt(_text, **kwargs):
            prompted.append(kwargs)
            return 'prompted'

        monkeypatch.setattr(click, 'prompt', _prompt)
        content = textwrap.dedent("""\
            label: '{{ label }}'
            account: '{{ account }}'
            metadata:
                template_variables:
                    label: {default: a-label}
                    account: {description: The account}
        """)
        result = process_template_content(content, interactive=True, template_vars={'label': 'given'})
        assert result == {'label': 'given', 'account': 'prompted'}
        assert len(prompted) == 1, 'only the variable left unresolved should be prompted for'

    def test_missing_variables_are_listed_sorted(self):
        """Every unresolved variable is named at once, in a stable order."""
        content = "a: '{{ zz }}'\nb: '{{ aa }}'\nc: '{{ mm }}'\n"
        with pytest.raises(click.BadParameter, match=r'template variables: aa, mm, zz\.'):
            process_template_content(content, interactive=False, template_vars={})

    def test_sandboxed_environment_refuses_attribute_access(self):
        """Configs are fetched from URLs, so a template must not be able to reach Python attributes.

        ``cycler`` is a Jinja2 global rather than an undeclared variable, so the payload rides along on any
        document that declares one legitimate variable, which every registry file does.
        """
        content = textwrap.dedent("""\
            label: '{{ cycler.__init__.__globals__ }}'
            hostname: '{{ host }}'
            metadata:
                template_variables:
                    host: {default: localhost}
        """)
        with pytest.raises(click.BadParameter, match=re.escape("access to attribute '__init__'")):
            process_template_content(content, interactive=False, template_vars={'host': 'h'})

    @pytest.mark.parametrize(
        ('content', 'match'),
        [
            pytest.param(':\ninvalid: [yaml', 'Invalid YAML', id='invalid_yaml'),
            pytest.param('- item1\n- item2\n', 'Expected a YAML mapping', id='non_dict_yaml'),
            pytest.param(
                "label: '{{ label }}'\nmetadata:\n  template_variables:\n    label:\n      description: x\n",
                r'No value provided for the template variables: label',
                id='missing_vars_non_interactive',
            ),
        ],
    )
    def test_invalid_input_raises(self, content, match):
        with pytest.raises(click.BadParameter, match=match):
            process_template_content(content, interactive=False)

    @pytest.mark.parametrize(
        ('metadata', 'match'),
        [
            pytest.param('just-a-string', 'The `metadata` section must be a mapping, got str', id='metadata_scalar'),
            pytest.param('\n  - a\n  - b', 'The `metadata` section must be a mapping, got list', id='metadata_list'),
            pytest.param(
                '\n  template_variables: oops',
                re.escape('`metadata.template_variables` must be a mapping, got str'),
                id='specs_scalar',
            ),
            pytest.param(
                '\n  template_variables:\n    label: a-description',
                re.escape('`metadata.template_variables.label` must be a mapping, got str'),
                id='spec_entry_scalar',
            ),
        ],
    )
    def test_malformed_metadata_raises_bad_parameter(self, metadata, match):
        """A malformed ``metadata`` section must not surface as a raw ``AttributeError``.

        The section comes from a file that may have been fetched over HTTP, so every shape of it has to reach the
        user as an actionable message rather than as Python internals.
        """
        content = f"label: '{{{{ label }}}}'\nmetadata: {metadata}\n"
        with pytest.raises(click.BadParameter, match=match):
            process_template_content(content, interactive=False, template_vars={'label': 'x'})

    def test_malformed_metadata_tolerated_without_placeholders(self):
        """A config that uses no placeholders is unaffected: ``metadata`` is still just stripped."""
        result = process_template_content('label: plain\nmetadata: just-a-string\n', interactive=False)
        assert result == {'label': 'plain'}

    def test_non_mapping_after_rendering_raises(self):
        """The renderer refuses a non-mapping result rather than returning it against its annotation."""
        with pytest.raises(click.BadParameter, match='Expected a YAML mapping after template rendering, got str'):
            _render_template("'{{ value }}'\n", {'value': 'a-scalar'})

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
        result = process_template_content(
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
        result = process_template_content(content, interactive=False, template_vars={'code_binary_name': 'pw'})
        assert result['label'] == 'pw-7.4'
        assert result['default_calc_job_plugin'] == 'quantumespresso.pw'
        assert result['filepath_executable'] == '/opt/bin/pw.x'
        assert 'metadata' not in result


class TestLoadContent:
    """Tests for :func:`_load_content` -- reading raw content from a path or URL."""

    def test_from_file(self, tmp_path):
        filepath = tmp_path / 'config.yaml'
        filepath.write_text('label: my-computer\nhostname: localhost\n')
        assert _load_content(str(filepath)) == 'label: my-computer\nhostname: localhost\n'

    def test_from_url(self, monkeypatch):
        """Loading from a URL fetches the content."""
        import requests

        monkeypatch.setattr(requests, 'get', lambda *a, **kw: _FakeResponse('label: url-computer\n'))
        assert _load_content('https://example.com/config.yaml') == 'label: url-computer\n'

    def test_file_not_found(self):
        with pytest.raises(click.BadParameter, match='Failed to read file'):
            _load_content('/nonexistent/path.yaml')

    def test_url_failure(self, monkeypatch):
        """A failing URL request raises ``click.BadParameter``."""
        import requests

        monkeypatch.setattr(requests, 'get', lambda *a, **kw: (_ for _ in ()).throw(requests.ConnectionError('fail')))
        with pytest.raises(click.BadParameter, match='Failed to fetch URL'):
            _load_content('https://example.com/config.yaml')


class TestParseTemplateVars:
    """Tests for :func:`parse_template_vars` -- file / URL / JSON resolution chain."""

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

        monkeypatch.setattr(requests, 'get', lambda *a, **kw: _FakeResponse('account: remote_project\n'))
        result = parse_template_vars('https://example.com/vars.yaml')
        assert result == {'account': 'remote_project'}

    def test_non_string_keys_raise(self, tmp_path):
        """YAML turns an unquoted ``1:`` into an int, which cannot become a Jinja2 keyword argument."""
        filepath = tmp_path / 'vars.yaml'
        filepath.write_text('1: x\ntrue: y\n')
        with pytest.raises(click.BadParameter, match='must use string keys for the variable names'):
            parse_template_vars(str(filepath))

    def test_nonexistent_path_names_all_accepted_forms(self):
        """A mistyped path must not be reported as merely invalid JSON."""
        with pytest.raises(
            click.BadParameter,
            match=re.escape('`vars.yaml` is not an existing file, a URL, or a valid inline JSON mapping'),
        ):
            parse_template_vars('vars.yaml')

    @pytest.mark.parametrize(
        ('value', 'match'),
        [
            pytest.param('not valid json', 'not an existing file, a URL, or a valid inline JSON', id='invalid_json'),
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

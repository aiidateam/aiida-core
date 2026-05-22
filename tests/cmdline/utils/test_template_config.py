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
)


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

    @pytest.mark.parametrize(
        ('content', 'match'),
        [
            (':\ninvalid: [yaml', 'Invalid YAML'),
            ('- item1\n- item2\n', 'Expected a YAML mapping'),
            (
                "label: '{{ label }}'\nmetadata:\n  template_variables:\n    label:\n      description: x\n",
                r'Template variables detected.*but no values provided',
            ),
        ],
        ids=['invalid_yaml', 'non_dict_yaml', 'missing_vars_non_interactive'],
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
        assert result['label'] == 'eiger-mc'
        assert '#SBATCH --partition=normal' in result['prepend_text']
        assert '#SBATCH --account=my_project' in result['prepend_text']
        assert '{username}' in result['work_dir']
        assert '{tot_num_mpiprocs}' in result['mpirun_command']
        assert 'metadata' not in result

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

    def test_file_not_found(self):
        with pytest.raises(click.BadParameter, match='Failed to read file'):
            load_and_process_template('/nonexistent/path.yaml', interactive=False)

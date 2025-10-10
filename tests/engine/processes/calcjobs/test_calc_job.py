###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `CalcJob` process sub class."""

import io
import json
import os
import pathlib
import tempfile
import uuid
from copy import deepcopy
from functools import partial
from unittest.mock import patch

import pytest

from aiida import orm
from aiida.common import CalcJobState, LinkType, StashMode, exceptions
from aiida.common.datastructures import FileCopyOperation
from aiida.engine import CalcJob, CalcJobImporter, ExitCode, Process, launch
from aiida.engine.processes.calcjobs.calcjob import validate_monitors, validate_stash_options
from aiida.engine.processes.calcjobs.monitors import CalcJobMonitorAction, CalcJobMonitorResult
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.utils import instantiate_process
from aiida.plugins import CalculationFactory, ParserFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')
ArithmeticAddParser = ParserFactory('core.arithmetic.add')


def raise_exception(exception, *args, **kwargs):
    """Raise an exception of the specified class.

    :param exception: exception class to raise
    """
    raise exception()


@pytest.fixture
def get_calcjob_builder(aiida_code_installed):
    """Return a builder for the ``ArithmeticAddCalculation`` that is ready to go."""

    def _factory(**kwargs):
        code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='bash')
        builder = code.get_builder()
        builder.x = orm.Int(1)
        builder.y = orm.Int(1)
        builder._update(**kwargs)
        return builder

    return _factory


@pytest.mark.requires_rmq
class DummyCalcJob(CalcJob):
    """`DummyCalcJob` implementation to test the calcinfo with container code."""

    @classmethod
    def define(cls, spec):
        super().define(spec)

    def prepare_for_submission(self, folder):
        from aiida.common.datastructures import CalcInfo, CodeInfo

        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = ['--version', '-c']
        codeinfo.stdin_name = 'aiida.in'
        codeinfo.stdout_name = 'aiida.out'
        codeinfo.stderr_name = 'aiida.err'

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]

        return calcinfo


@pytest.mark.requires_rmq
class FileCalcJob(CalcJob):
    """Example `CalcJob` implementation to test the `provenance_exclude_list` functionality.

    The content of the input `files` will be copied to the `folder` sandbox, but also added to the attribute
    `provenance_exclude_list` of the `CalcInfo` which should instruct the engine to copy the files to the remote work
    directory but NOT to the repository of the `CalcJobNode`.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('settings', valid_type=orm.Dict)
        spec.input_namespace('files', valid_type=orm.SinglefileData, dynamic=True)

    def prepare_for_submission(self, folder):
        from aiida.common.datastructures import CalcInfo, CodeInfo

        for key, node in self.inputs.files.items():
            filepath = key.replace('_', os.sep)
            dirname = os.path.dirname(filepath)
            basename = os.path.basename(filepath)
            with node.open(mode='rb') as source:
                if dirname:
                    subfolder = folder.get_subfolder(dirname, create=True)
                    subfolder.create_file_from_filelike(source, basename)
                else:
                    folder.create_file_from_filelike(source, filepath)

        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.provenance_exclude_list = self.inputs.settings.base.attributes.get('provenance_exclude_list')
        return calcinfo


@pytest.mark.requires_rmq
class MultiCodesCalcJob(CalcJob):
    """`MultiCodesCalcJob` implementation to test the calcinfo with multiple codes set.

    The codes are run in parallel and each code enforces a different value for ``withmpi`` on the ``CodeInfo``.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('code_info_with_mpi_none', valid_type=orm.AbstractCode, required=False)
        spec.input('code_info_with_mpi_true', valid_type=orm.AbstractCode, required=False)
        spec.input('code_info_with_mpi_false', valid_type=orm.AbstractCode, required=False)
        spec.input('parallel_run', valid_type=orm.Bool, default=lambda: orm.Bool(True))

    def prepare_for_submission(self, folder):
        from aiida.common.datastructures import CalcInfo, CodeInfo, CodeRunMode

        calc_info = CalcInfo()
        calc_info.codes_info = []

        for key, with_mpi in [
            ('code_info_with_mpi_none', None),
            ('code_info_with_mpi_true', True),
            ('code_info_with_mpi_false', False),
        ]:
            if key in self.inputs:
                code_info = CodeInfo()
                code_info.code_uuid = self.inputs[key].uuid
                if with_mpi is not None:
                    code_info.withmpi = with_mpi
                calc_info.codes_info.append(code_info)

        if self.inputs.parallel_run:
            calc_info.codes_run_mode = CodeRunMode.PARALLEL
        else:
            calc_info.codes_run_mode = CodeRunMode.SERIAL

        return calc_info


@pytest.mark.parametrize(
    'code_key, with_mpi_code, with_mpi_option, with_mpi_option_default, expected',
    (
        ('code_info_with_mpi_none', None, True, True, 3),
        ('code_info_with_mpi_none', None, False, True, 0),
        ('code_info_with_mpi_none', None, None, False, 0),
        ('code_info_with_mpi_none', None, None, True, 3),
        ('code_info_with_mpi_none', True, True, True, 3),
        ('code_info_with_mpi_none', True, False, True, None),
        ('code_info_with_mpi_none', False, True, True, None),
        ('code_info_with_mpi_none', False, False, True, 0),
        ('code_info_with_mpi_true', None, True, True, 3),
        ('code_info_with_mpi_true', None, False, True, None),
        ('code_info_with_mpi_true', None, None, True, 3),
        ('code_info_with_mpi_true', True, True, True, 3),
        ('code_info_with_mpi_true', True, False, True, None),
        ('code_info_with_mpi_true', False, True, True, None),
        ('code_info_with_mpi_true', False, False, True, None),
        ('code_info_with_mpi_false', None, True, True, None),
        ('code_info_with_mpi_false', None, False, True, 0),
        ('code_info_with_mpi_false', None, None, True, 0),
        ('code_info_with_mpi_false', True, True, True, None),
        ('code_info_with_mpi_false', True, False, True, None),
        ('code_info_with_mpi_false', False, True, True, None),
        ('code_info_with_mpi_false', False, False, True, 0),
    ),
)
def test_multi_codes_with_mpi(
    aiida_code_installed,
    fixture_sandbox,
    manager,
    code_key,
    with_mpi_code,
    with_mpi_option,
    with_mpi_option_default,
    expected,
):
    """Test the functionality that controls whether the calculation is to be run with MPI.

    The value specified by the ``metadata.options.withmpi`` input is the default. This value can be overidden by either
    the plugin (through the ``CodeInfo.withmpi`` attribute) or the code input (through the ``AbstractCode.with_mpi``
    property). If both of these are explicitly defined, i.e. are not ``None``, they have to be equivalent or an
    exception is raised. The parametrization represents the matrix of all possible combinations. If the final value for
    ``with_mpi`` is ``True`` we can check that this is correctly propagated by checking the length of the
    ``prepend_cmdline_params`` list in the ``codes_info`` which should not be empty. Since the ``presubmit`` method does
    not return this value directly but writes it to a file in the sandbox, we have to read and deserialize it first.
    """
    from aiida.engine.utils import instantiate_process

    inputs = {
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'),
        code_key: aiida_code_installed(
            default_calc_job_plugin='core.arithmetic.add',
            filepath_executable='/bin/bash',
            label=str(uuid.uuid4()),
            with_mpi=with_mpi_code,
        ),
        'metadata': {
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
            }
        },
    }

    class SubMultiCodesCalcJob(MultiCodesCalcJob):
        """Subclass to override the default for the ``withmpi`` option."""

        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.inputs['metadata']['options']['withmpi'].default = with_mpi_option_default

    if with_mpi_option is not None:
        inputs['metadata']['options']['withmpi'] = with_mpi_option

    process = instantiate_process(manager.get_runner(), SubMultiCodesCalcJob, **inputs)

    if expected is None:
        with pytest.raises(RuntimeError, match=r'Inconsistent requirements as to whether'):
            process.presubmit(fixture_sandbox)
        return

    process.presubmit(fixture_sandbox)

    with fixture_sandbox.get_subfolder('.aiida').open('job_tmpl.json') as handle:
        job_tmpl = json.load(handle)

    assert len(job_tmpl['codes_info'][0]['prepend_cmdline_params']) == expected


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
@pytest.mark.parametrize('parallel_run', [True, False])
def test_multi_codes_run_parallel(aiida_code_installed, file_regression, parallel_run):
    """Test codes_run_mode set in CalcJob"""
    inputs = {
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'),
        'code_info_with_mpi_none': aiida_code_installed(
            default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash', label=str(uuid.uuid4())
        ),
        'code_info_with_mpi_false': aiida_code_installed(
            default_calc_job_plugin='core.arithmetic.add',
            filepath_executable='/bin/bash',
            label=str(uuid.uuid4()),
            with_mpi=False,
        ),
        'parallel_run': orm.Bool(parallel_run),
        'metadata': {'dry_run': True, 'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}},
    }

    _, node = launch.run_get_node(MultiCodesCalcJob, **inputs)
    folder_name = node.dry_run_info['folder']
    submit_script_filename = node.get_option('submit_script_filename')
    with open(os.path.join(folder_name, submit_script_filename), encoding='utf8') as handle:
        content = handle.read()

    file_regression.check(content, extension='.sh')


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
@pytest.mark.parametrize('computer_use_double_quotes', [True, False])
def test_computer_double_quotes(
    aiida_computer_local, aiida_code_installed, file_regression, computer_use_double_quotes
):
    """Test that bash script quote escape behaviour can be controlled"""
    computer = aiida_computer_local(label=f'test-code-computer-{computer_use_double_quotes}')
    computer.set_use_double_quotes(computer_use_double_quotes)

    inputs = {
        'code': aiida_code_installed(
            default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash', computer=computer
        ),
        'metadata': {
            'dry_run': True,
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                'withmpi': True,
            },
        },
    }

    _, node = launch.run_get_node(DummyCalcJob, **inputs)
    folder_name = node.dry_run_info['folder']
    submit_script_filename = node.get_option('submit_script_filename')
    with open(os.path.join(folder_name, submit_script_filename), encoding='utf8') as handle:
        content = handle.read()

    file_regression.check(content, extension='.sh')


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
@pytest.mark.parametrize('code_use_double_quotes', [True, False])
def test_code_double_quotes(aiida_localhost, file_regression, code_use_double_quotes):
    """Test that bash script quote escape behaviour can be controlled"""
    code = orm.InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash')
    code.use_double_quotes = code_use_double_quotes
    inputs = {
        'code': code.store(),
        'metadata': {
            'dry_run': True,
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                'withmpi': True,
            },
        },
    }

    _, node = launch.run_get_node(DummyCalcJob, **inputs)
    folder_name = node.dry_run_info['folder']
    submit_script_filename = node.get_option('submit_script_filename')
    with open(os.path.join(folder_name, submit_script_filename), encoding='utf8') as handle:
        content = handle.read()

    file_regression.check(content, extension='.sh')


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
def test_containerized_code(file_regression, aiida_localhost):
    """Test the :class:`~aiida.orm.nodes.data.code.containerized.ContainerizedCode`."""
    aiida_localhost.set_use_double_quotes(True)
    engine_command = """singularity exec --bind $PWD:$PWD {image_name}"""
    containerized_code = orm.ContainerizedCode(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/bash',
        engine_command=engine_command,
        image_name='ubuntu',
        computer=aiida_localhost,
    ).store()

    inputs = {
        'code': containerized_code,
        'metadata': {
            'dry_run': True,
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                'withmpi': False,
            },
        },
    }

    _, node = launch.run_get_node(DummyCalcJob, **inputs)
    folder_name = node.dry_run_info['folder']
    submit_script_filename = node.get_option('submit_script_filename')
    content = (pathlib.Path(folder_name) / submit_script_filename).read_text()

    file_regression.check(content, extension='.sh')


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
def test_containerized_code_wrap_cmdline_params(file_regression, aiida_localhost):
    """Test :class:`~aiida.orm.nodes.data.code.containerized.ContainerizedCode` with ``wrap_cmdline_params = True``."""
    aiida_localhost.set_use_double_quotes(False)
    engine_command = """docker run -i -v $PWD:/workdir:rw -w /workdir {image_name} sh -c"""
    containerized_code = orm.ContainerizedCode(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/bash',
        engine_command=engine_command,
        image_name='ubuntu',
        computer=aiida_localhost,
        wrap_cmdline_params=True,
    ).store()

    inputs = {
        'code': containerized_code,
        'metadata': {
            'dry_run': True,
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                'withmpi': False,
            },
        },
    }

    _, node = launch.run_get_node(DummyCalcJob, **inputs)
    folder_name = node.dry_run_info['folder']
    submit_script_filename = node.get_option('submit_script_filename')
    content = (pathlib.Path(folder_name) / submit_script_filename).read_text()

    file_regression.check(content, extension='.sh')


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
def test_containerized_code_withmpi_true(file_regression, aiida_localhost):
    """Test the :class:`~aiida.orm.nodes.data.code.containerized.ContainerizedCode` with ``withmpi=True``."""
    aiida_localhost.set_use_double_quotes(True)
    engine_command = """singularity exec --bind $PWD:$PWD {image_name}"""
    containerized_code = orm.ContainerizedCode(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/bash',
        engine_command=engine_command,
        image_name='ubuntu',
        computer=aiida_localhost,
    ).store()

    inputs = {
        'code': containerized_code,
        'metadata': {
            'dry_run': True,
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                'withmpi': True,
            },
        },
    }

    _, node = launch.run_get_node(DummyCalcJob, **inputs)
    folder_name = node.dry_run_info['folder']
    submit_script_filename = node.get_option('submit_script_filename')
    content = (pathlib.Path(folder_name) / submit_script_filename).read_text()

    file_regression.check(content, extension='.sh')


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('chdir_tmp_path')
def test_portable_code(tmp_path, aiida_localhost):
    """Test run container code"""
    (tmp_path / 'bash').write_bytes(b'bash implementation')
    subdir = tmp_path / 'sub'
    subdir.mkdir()
    (subdir / 'dummy').write_bytes(b'dummy')

    subsubdir = tmp_path / 'sub' / 'sub'
    subsubdir.mkdir()
    (subsubdir / 'sub-dummy').write_bytes(b'sub dummy')

    code = orm.PortableCode(
        filepath_executable='bash',
        filepath_files=tmp_path,
    ).store()

    inputs = {
        'code': code,
        'x': orm.Int(1),
        'y': orm.Int(2),
        'metadata': {
            'computer': aiida_localhost,
            'dry_run': True,
            'options': {},
        },
    }

    _, node = launch.run_get_node(ArithmeticAddCalculation, **inputs)
    folder_name = node.dry_run_info['folder']
    uploaded_files = os.listdir(folder_name)

    # Since the repository will only contain files on the top-level due to `Code.set_files` we only check those
    for filename in code.base.repository.list_object_names():
        assert filename in uploaded_files

    content = (pathlib.Path(folder_name) / code.filepath_executable).read_text()
    subcontent = (pathlib.Path(folder_name) / 'sub' / 'dummy').read_text()
    subsubcontent = (pathlib.Path(folder_name) / 'sub' / 'sub' / 'sub-dummy').read_text()

    assert content == 'bash implementation'
    assert subcontent == 'dummy'
    assert subsubcontent == 'sub dummy'


@pytest.mark.requires_rmq
class TestCalcJob:
    """Test for the `CalcJob` process sub class."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost, tmp_path):
        """Initialize the profile."""
        (tmp_path / 'bash').write_bytes(b'bash implementation')

        assert Process.current() is None
        self.computer = aiida_localhost
        self.remote_code = orm.InstalledCode(computer=self.computer, filepath_executable='/bin/bash').store()
        self.local_code = orm.PortableCode(filepath_executable='bash', filepath_files=tmp_path).store()
        self.inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'metadata': {'options': {}}}
        yield
        assert Process.current() is None

    def instantiate_process(self, state=CalcJobState.PARSING):
        """Instantiate a process with default inputs and return the `Process` instance."""
        from aiida.engine.utils import instantiate_process
        from aiida.manage import get_manager

        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory('core.arithmetic.add')
        process = instantiate_process(runner, process_class, **inputs)
        process.node.set_state(state)

        return process

    def test_get_hash(self, get_calcjob_builder):
        """Test that :meth:`aiida.orm.CalcJobNode.get_hash` returns the same hash as what is stored in the extras."""
        builder = get_calcjob_builder()
        _, node = launch.run_get_node(builder)
        assert node.base.extras.get(node.base.caching._HASH_EXTRA_KEY) == node.base.caching.get_hash()

    def test_get_objects_attributes(self, get_calcjob_builder):
        """Test that :meth:`aiida.orm.CalcJobNode._get_objects_to_hash` returns the expected objects."""
        builder = get_calcjob_builder()
        _, node = launch.run_get_node(builder)
        objects = node.base.caching.get_objects_to_hash()

        assert 'version' not in objects
        assert 'version' not in objects['attributes']

    def test_compute_hash_version_independent(self, get_calcjob_builder, monkeypatch, manager):
        """Test that :meth:`aiida.orm.CalcJobNode.compute_hash` is independent of the version of ``aiida-core``."""
        import aiida

        _, node_a = launch.run_get_node(get_calcjob_builder())

        monkeypatch.setattr(aiida, '__version__', '0.0.0')

        # The global runner uses an instance of the ``PluginVersionProvider`` that caches versions so need to reset it
        manager.reset_runner()

        _, node_b = launch.run_get_node(get_calcjob_builder())
        assert node_b.base.attributes.get('version')['core'] == '0.0.0'
        assert node_b.base.caching.compute_hash() == node_a.base.caching.compute_hash()
        assert node_b.base.caching.get_hash() == node_a.base.caching.get_hash()

    def test_process_status(self):
        """Test that the process status is properly reset if calculation ends successfully."""
        _, node = launch.run_get_node(ArithmeticAddCalculation, code=self.remote_code, **self.inputs)
        assert node.is_finished_ok
        assert node.process_status is None

    def test_run_base_class(self):
        """Verify that it is impossible to run, submit or instantiate a base `CalcJob` class."""
        with pytest.raises(exceptions.InvalidOperation):
            CalcJob()

        with pytest.raises(exceptions.InvalidOperation):
            launch.run(CalcJob)

        with pytest.raises(exceptions.InvalidOperation):
            launch.run_get_node(CalcJob)

        with pytest.raises(exceptions.InvalidOperation):
            launch.run_get_pk(CalcJob)

        with pytest.raises(exceptions.InvalidOperation):
            launch.submit(CalcJob)

    def test_define_not_calling_super(self):
        """A `CalcJob` that does not call super in `define` classmethod should raise."""

        class IncompleteDefineCalcJob(CalcJob):
            """Test class with incomplete define method"""

            @classmethod
            def define(cls, spec):
                pass

            def prepare_for_submission(self, folder):
                pass

        with pytest.raises(AssertionError):
            launch.run(IncompleteDefineCalcJob)

    def test_spec_options_property(self):
        """`CalcJob.spec_options` should return the options port namespace of its spec."""
        assert isinstance(CalcJob.spec_options, PortNamespace)
        assert CalcJob.spec_options == CalcJob.spec().inputs['metadata']['options']

    def test_invalid_options_type(self):
        """Verify that passing an invalid type to `metadata.options` raises a `TypeError`."""

        class SimpleCalcJob(CalcJob):
            """Simple `CalcJob` implementation"""

            @classmethod
            def define(cls, spec):
                super().define(spec)

            def prepare_for_submission(self, folder):
                pass

        # The `metadata.options` input expects a plain dict and not a node `Dict`
        with pytest.raises(TypeError):
            launch.run(SimpleCalcJob, code=self.remote_code, metadata={'options': orm.Dict(dict={'a': 1})})

    def test_remote_code_set_computer_implicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work, because the `computer` should be retrieved from the `code` and automatically set for the
        process by the engine itself.
        """
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        process = ArithmeticAddCalculation(inputs=inputs)
        assert process.node.is_stored
        assert process.node.computer.uuid == self.remote_code.computer.uuid

    def test_remote_code_unstored_computer(self):
        """Test launching a `CalcJob` with an unstored computer which should raise."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['computer'] = orm.Computer('different', 'localhost', 'desc', 'core.local', 'core.direct')

        with pytest.raises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_remote_code_set_computer_explicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work as long as the explicitly defined computer is the same as the one configured for the `code`
        input. If this is not the case, it should raise.
        """
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        # Setting explicitly a computer that is not the same as that of the `code` should raise
        with pytest.raises(ValueError):
            inputs['metadata']['computer'] = orm.Computer(
                'different', 'localhost', 'desc', 'core.local', 'core.direct'
            ).store()
            process = ArithmeticAddCalculation(inputs=inputs)

        # Setting the same computer as that of the `code` effectively accomplishes nothing but should be fine
        inputs['metadata']['computer'] = self.remote_code.computer
        process = ArithmeticAddCalculation(inputs=inputs)
        assert process.node.is_stored
        assert process.node.computer.uuid == self.remote_code.computer.uuid

    def test_local_code_set_computer(self):
        """Test launching a `CalcJob` with a local code *with* explicitly defining a computer, which should work."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code
        inputs['metadata']['computer'] = self.computer

        process = ArithmeticAddCalculation(inputs=inputs)
        assert process.node.is_stored
        assert process.node.computer.uuid == self.computer.uuid

    def test_local_code_no_computer(self):
        """Test launching a `CalcJob` with a local code *without* explicitly defining a computer, which should raise."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code

        with pytest.raises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_parser_name(self):
        """Passing an invalid parser name should already stop during input validation."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['parser_name'] = 'invalid_parser'

        with pytest.raises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_resources(self):
        """Passing invalid resources should already stop during input validation."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['resources'] = {'num_machines': 'invalid_type'}

        with pytest.raises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_par_env_resources_computer(self):
        """Test launching a `CalcJob` an a computer with a scheduler using `ParEnvJobResource` as resources.

        Even though the computer defines a default number of MPI procs per machine, it should not raise when the
        scheduler that is defined does not actually support it, for example SGE or LSF.
        """
        inputs = deepcopy(self.inputs)
        computer = orm.Computer('sge_computer', 'localhost', 'desc', 'core.local', 'core.sge').store()
        computer.set_default_mpiprocs_per_machine(1)

        inputs['code'] = orm.InstalledCode(computer=computer, filepath_executable='/bin/bash').store()
        inputs['metadata']['options']['resources'] = {'parallel_env': 'environment', 'tot_num_mpiprocs': 10}

        # Just checking that instantiating does not raise, meaning the inputs were valid
        ArithmeticAddCalculation(inputs=inputs)

    @pytest.mark.timeout(5)
    @patch.object(CalcJob, 'presubmit', partial(raise_exception, exceptions.InputValidationError))
    def test_exception_presubmit(self):
        """Test that an exception in the presubmit circumvents the exponential backoff and just excepts the process.

        The `presubmit` call of the `CalcJob` is now called in `aiida.engine.processes.calcjobs.tasks.task_upload_job`
        which is wrapped in the exponential backoff mechanism. The latter was introduced to recover from transient
        problems such as connection problems during the actual upload to a remote machine. However, it should not catch
        exceptions from the `presubmit` call which are not actually transient and thus not automatically recoverable. In
        this case the process should simply except. Here we test this by mocking the presubmit to raise an exception and
        check that it is bubbled up and the process does not end up in a paused state.
        """
        from aiida.engine.processes.calcjobs.tasks import PreSubmitException

        with pytest.raises(PreSubmitException, match='exception occurred in presubmit call'):
            launch.run(ArithmeticAddCalculation, code=self.remote_code, **self.inputs)

    @pytest.mark.usefixtures('chdir_tmp_path')
    def test_run_local_code(self):
        """Run a dry-run with local code."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code
        inputs['metadata']['computer'] = self.computer
        inputs['metadata']['dry_run'] = True

        # The following will run `upload_calculation` which will test that uploading files works correctly
        _, node = launch.run_get_node(ArithmeticAddCalculation, **inputs)
        uploaded_files = os.listdir(node.dry_run_info['folder'])

        # Since the repository will only contain files on the top-level due to `Code.set_files` we only check those
        for filename in self.local_code.base.repository.list_object_names():
            assert filename in uploaded_files

    @pytest.mark.usefixtures('chdir_tmp_path')
    def test_rerunnable(self):
        """Test that setting `rerunnable` in the options results in it being set in the job template."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code
        inputs['metadata']['computer'] = self.computer
        inputs['metadata']['dry_run'] = True
        inputs['metadata']['options']['rerunnable'] = True

        _, node = launch.run_get_node(ArithmeticAddCalculation, **inputs)
        job_tmpl_file = os.path.join(node.dry_run_info['folder'], '.aiida', 'job_tmpl.json')

        with open(job_tmpl_file, mode='r', encoding='utf8') as in_f:
            job_tmpl = json.load(in_f)

        assert job_tmpl['rerunnable']

    @pytest.mark.usefixtures('chdir_tmp_path')
    def test_provenance_exclude_list(self):
        """Test the functionality of the `CalcInfo.provenance_exclude_list` attribute."""
        code = orm.InstalledCode(
            default_calc_job_plugin='core.arithmetic.add', computer=self.computer, filepath_executable='/bin/true'
        ).store()

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write('dummy_content')
            handle.flush()
            file_one = orm.SinglefileData(file=handle.name)

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write('dummy_content')
            handle.flush()
            file_two = orm.SinglefileData(file=handle.name)

        inputs = {
            'code': code,
            'files': {
                # Note the `FileCalcJob` will turn underscores in the key into forward slashes making a nested hierarchy
                'base_a_sub_one': file_one,
                'base_b_two': file_two,
            },
            'settings': orm.Dict(dict={'provenance_exclude_list': ['base/a/sub/one']}),
            'metadata': {'dry_run': True, 'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}},
        }

        # We perform a `dry_run` because the calculation cannot actually run, however, the contents will still be
        # written to the node's repository so we can check it contains the expected contents.
        _, node = launch.run_get_node(FileCalcJob, **inputs)

        assert 'folder' in node.dry_run_info

        # Verify that the folder (representing the node's repository) indeed do not contain the input files. Note,
        # however, that the directory hierarchy should be there, albeit empty
        assert 'base' in node.base.repository.list_object_names()
        assert sorted(['b']) == sorted(node.base.repository.list_object_names(os.path.join('base')))
        assert ['two'] == node.base.repository.list_object_names(os.path.join('base', 'b'))

    def test_parse_no_retrieved_folder(self):
        """Test the `CalcJob.parse` method when there is no retrieved folder."""
        process = self.instantiate_process()
        exit_code = process.parse()
        assert exit_code == process.exit_codes.ERROR_NO_RETRIEVED_FOLDER

    def test_parse_retrieved_folder(self):
        """Test the `CalcJob.parse` method when there is a retrieved folder."""
        process = self.instantiate_process()
        retrieved = orm.FolderData().store()
        retrieved.base.links.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)
        exit_code = process.parse()

        # The following exit code is specific to the `ArithmeticAddCalculation` we are testing here and is returned
        # because the retrieved folder does not contain the output file it expects
        assert exit_code == process.exit_codes.ERROR_READING_OUTPUT_FILE

    def test_get_importer(self):
        """Test the ``CalcJob.get_importer`` method."""
        assert isinstance(ArithmeticAddCalculation.get_importer(), CalcJobImporter)
        assert isinstance(
            ArithmeticAddCalculation.get_importer(entry_point_name='core.arithmetic.add'), CalcJobImporter
        )

        with pytest.raises(exceptions.MissingEntryPointError):
            ArithmeticAddCalculation.get_importer(entry_point_name='non-existing')


@pytest.fixture
def generate_process(aiida_code_installed):
    """Instantiate a process with default inputs and return the `Process` instance."""
    from aiida.engine.utils import instantiate_process
    from aiida.manage import get_manager

    def _generate_process(inputs=None):
        base_inputs = {
            'code': aiida_code_installed(
                default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'
            ),
            'x': orm.Int(1),
            'y': orm.Int(2),
            'metadata': {'options': {}},
        }

        if inputs is not None:
            base_inputs = {**base_inputs, **inputs}

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory('core.arithmetic.add')
        process = instantiate_process(runner, process_class, **base_inputs)
        process.node.set_state(CalcJobState.PARSING)

        return process

    return _generate_process


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('override_logging')
def test_parse_insufficient_data(generate_process):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    Here we check explicitly that the parsing does not except even if the required information is not available.
    """
    process = generate_process()

    retrieved = orm.FolderData().store()
    retrieved.base.links.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)
    process.parse()

    filename_stderr = process.node.get_option('scheduler_stderr')
    filename_stdout = process.node.get_option('scheduler_stdout')

    # The scheduler parsing requires three resources of information, the `detailed_job_info` dictionary which is
    # stored as an attribute on the calculation job node and the output of the stdout and stderr which are both
    # stored in the repository. In this test, we haven't created these on purpose. This should not except the
    # process but should log a warning, so here we check that those expected warnings are attached to the node
    logs = [log.message for log in orm.Log.collection.get_logs_for(process.node)]
    expected_logs = [
        'could not parse scheduler output: the `detailed_job_info` attribute is missing',
        f'could not parse scheduler output: the `{filename_stderr}` file is missing',
        f'could not parse scheduler output: the `{filename_stdout}` file is missing',
    ]

    for log in expected_logs:
        assert log in logs


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('override_logging')
def test_parse_non_zero_retval(generate_process):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    This is testing the case where the `detailed_job_info` is incomplete because the call failed. This is checked
    through the return value that is stored within the attribute dictionary.
    """
    process = generate_process()

    retrieved = orm.FolderData().store()
    retrieved.base.links.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    process.node.base.attributes.set('detailed_job_info', {'retval': 1, 'stderr': 'accounting disabled', 'stdout': ''})
    process.parse()

    logs = [log.message for log in orm.Log.collection.get_logs_for(process.node)]
    assert 'could not parse scheduler output: return value of `detailed_job_info` is non-zero' in logs


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('override_logging')
def test_parse_not_implemented(generate_process):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    Here we check explicitly that the parsing does not except even if the scheduler does not implement the method.
    """
    process = generate_process()

    retrieved = orm.FolderData()
    retrieved.base.links.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    process.node.base.attributes.set('detailed_job_info', {})

    filename_stderr = process.node.get_option('scheduler_stderr')
    filename_stdout = process.node.get_option('scheduler_stdout')

    retrieved.base.repository.put_object_from_filelike(io.BytesIO(b'\n'), filename_stderr)
    retrieved.base.repository.put_object_from_filelike(io.BytesIO(b'\n'), filename_stdout)
    retrieved.store()

    process.parse()

    # The `DirectScheduler` at this point in time does not implement the `parse_output` method. Instead of raising
    # a warning message should be logged. We verify here that said message is present.
    logs = [log.message for log in orm.Log.collection.get_logs_for(process.node)]
    expected_logs = ['`DirectScheduler` does not implement scheduler output parsing']

    for log in expected_logs:
        assert log in logs


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('override_logging')
def test_parse_scheduler_excepted(generate_process, monkeypatch):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    Here we check explicitly the case where the `Scheduler.parse_output` method excepts
    """
    from aiida.schedulers.plugins.direct import DirectScheduler

    process = generate_process()

    retrieved = orm.FolderData()
    retrieved.base.links.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    process.node.base.attributes.set('detailed_job_info', {})

    filename_stderr = process.node.get_option('scheduler_stderr')
    filename_stdout = process.node.get_option('scheduler_stdout')

    retrieved.base.repository.put_object_from_filelike(io.BytesIO(b'\n'), filename_stderr)
    retrieved.base.repository.put_object_from_filelike(io.BytesIO(b'\n'), filename_stdout)
    retrieved.store()

    msg = 'crash'

    def raise_exception(*args, **kwargs):
        raise RuntimeError(msg)

    # Monkeypatch the `DirectScheduler.parse_output` to raise an exception
    monkeypatch.setattr(DirectScheduler, 'parse_output', raise_exception)
    process.parse()
    logs = [log.message for log in orm.Log.collection.get_logs_for(process.node)]
    expected_logs = [f'the `parse_output` method of the scheduler excepted: {msg}']

    for log in expected_logs:
        assert log in logs


@pytest.mark.requires_rmq
@pytest.mark.parametrize(
    ('exit_status_scheduler', 'exit_status_retrieved', 'final'),
    (
        (None, None, 0),
        (100, None, 100),
        (None, 400, 400),
        (100, 400, 400),
        (100, 0, 0),
    ),
)
def test_parse_exit_code_priority(
    exit_status_scheduler,
    exit_status_retrieved,
    final,
    generate_calc_job,
    fixture_sandbox,
    aiida_code_installed,
    monkeypatch,
):
    """Test the logic around exit codes in the `CalcJob.parse` method.

    The `parse` method will first call the `Scheduler.parse_output` method, which if implemented by the relevant
    scheduler plugin, will parse the scheduler output and potentially return an exit code. Next, the output parser
    plugin is called if defined in the inputs that can also optionally return an exit code. This test is designed
    to make sure the right logic is implemented in terms of which exit code should be dominant.

    Scheduler result | Retrieved result | Final result    | Scenario
    -----------------|------------------|-----------------|-----------------------------------------
    `None`           | `None`           | `ExitCode(0)`   | Neither parser found any problem
    `ExitCode(100)`  | `None`           | `ExitCode(100)` | Scheduler found issue, output parser does not override
    `None`           | `ExitCode(400)`  | `ExitCode(400)` | Only output parser found a problem
    `ExitCode(100)`  | `ExitCode(400)`  | `ExitCode(400)` | Scheduler found issue, but output parser overrides
                     |                  |                 | with a more specific error code
    `ExitCode(100)`  | `ExitCode(0)`    | `ExitCode(0)`   | Scheduler found issue but output parser overrides saying
                     |                  |                 | that despite that the calculation should be considered
                     |                  |                 | finished successfully.

    To test this, we just need to test the `CalcJob.parse` method and the easiest way is to simply mock the scheduler
    parser and output parser calls called `parse_scheduler_output` and `parse_retrieved_output`, respectively. We will
    just mock them by a simple method that returns `None` or an `ExitCode`. We then check that the final exit code
    returned by `CalcJob.parse` is the one we expect according to the table above.
    """
    from aiida.orm import Int

    def parse_scheduler_output(_, __):
        if exit_status_scheduler is not None:
            return ExitCode(exit_status_scheduler)

    def parse_retrieved_output(_, __):
        if exit_status_retrieved is not None:
            return ExitCode(exit_status_retrieved)

    monkeypatch.setattr(CalcJob, 'parse_scheduler_output', parse_scheduler_output)
    monkeypatch.setattr(CalcJob, 'parse_retrieved_output', parse_retrieved_output)

    inputs = {
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'),
        'x': Int(1),
        'y': Int(2),
    }
    process = generate_calc_job(fixture_sandbox, 'core.arithmetic.add', inputs, return_process=True)
    retrieved = orm.FolderData().store()
    retrieved.base.links.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    result = process.parse()
    assert isinstance(result, ExitCode)
    assert result.status == final


@pytest.mark.requires_rmq
def test_additional_retrieve_list(generate_process, fixture_sandbox):
    """Test the ``additional_retrieve_list`` option."""
    process = generate_process()
    process.presubmit(fixture_sandbox)
    retrieve_list = process.node.base.attributes.get('retrieve_list')

    # Keep reference of the base contents of the retrieve list.
    base_retrieve_list = retrieve_list

    # Test that the code works if no explicit additional retrieve list is specified
    assert len(retrieve_list) != 0
    assert isinstance(process.node.base.attributes.get('retrieve_list'), list)

    # Defining explicit additional retrieve list that is disjoint with the base retrieve list
    additional_retrieve_list = ['file.txt', 'folder/file.txt']
    process = generate_process({'metadata': {'options': {'additional_retrieve_list': additional_retrieve_list}}})
    process.presubmit(fixture_sandbox)
    retrieve_list = process.node.base.attributes.get('retrieve_list')

    # Check that the `retrieve_list` is a list and contains the union of the base and additional retrieve list
    assert isinstance(process.node.base.attributes.get('retrieve_list'), list)
    assert set(retrieve_list) == set(base_retrieve_list).union(set(additional_retrieve_list))

    # Defining explicit additional retrieve list with elements that overlap with `base_retrieve_list
    additional_retrieve_list = ['file.txt', 'folder/file.txt'] + base_retrieve_list
    process = generate_process({'metadata': {'options': {'additional_retrieve_list': additional_retrieve_list}}})
    process.presubmit(fixture_sandbox)
    retrieve_list = process.node.base.attributes.get('retrieve_list')

    # Check that the `retrieve_list` is a list and contains the union of the base and additional retrieve list
    assert isinstance(process.node.base.attributes.get('retrieve_list'), list)
    assert set(retrieve_list) == set(base_retrieve_list).union(set(additional_retrieve_list))

    # Test the validator
    with pytest.raises(ValueError, match=r'`additional_retrieve_list` should only contain relative filepaths.*'):
        process = generate_process({'metadata': {'options': {'additional_retrieve_list': [None]}}})

    with pytest.raises(ValueError, match=r'`additional_retrieve_list` should only contain relative filepaths.*'):
        process = generate_process({'metadata': {'options': {'additional_retrieve_list': ['/abs/path']}}})


@pytest.mark.parametrize(
    ('stash_options', 'expected'),
    (
        ({'target_base': None}, '`metadata.options.stash.target_base` should be'),
        ({'target_base': 'relative/path'}, '`metadata.options.stash.target_base` should be'),
        ({'target_base': '/path'}, '`metadata.options.stash.source_list` should be'),
        ({'target_base': '/path', 'source_list': ['/abspath']}, '`metadata.options.stash.source_list` should be'),
        (
            {'target_base': '/path', 'source_list': ['rel/path'], 'stash_mode': 'test'},
            '`metadata.options.stash.stash_mode` should be',
        ),
        ({'target_base': '/path', 'source_list': ['rel/path']}, '`metadata.options.stash.stash_mode` should be'),
        ({'target_base': '/path', 'source_list': ['rel/path'], 'stash_mode': StashMode.COPY.value}, None),
        (
            {'target_base': '/path', 'source_list': ['rel/path'], 'stash_mode': StashMode.COMPRESS_TAR.value},
            '`metadata.options.stash.dereference` should be',
        ),
        (
            {
                'target_base': '/path',
                'source_list': ['rel/path'],
                'stash_mode': StashMode.COMPRESS_TAR.value,
                'dereference': 'True',
            },
            '`metadata.options.stash.dereference` should be',
        ),
        (
            {
                'target_base': '/path',
                'source_list': ['rel/path'],
                'stash_mode': StashMode.COMPRESS_TARBZ2.value,
                'dereference': True,
            },
            None,
        ),
        (
            {
                'target_base': '/path',
                'source_list': ['rel/path'],
                'stash_mode': StashMode.COMPRESS_TARGZ.value,
                'dereference': True,
            },
            None,
        ),
        (
            {
                'target_base': '/path',
                'source_list': ['rel/path'],
                'stash_mode': StashMode.COMPRESS_TARXZ.value,
                'dereference': True,
            },
            None,
        ),
        (
            {
                'target_base': '/path',
                'source_list': ['rel/path'],
                'stash_mode': StashMode.COPY.value,
                'dereference': True,
            },
            '`metadata.options.stash.dereference` is only valid for compression stashing modes',
        ),
    ),
)
def test_validate_stash_options(stash_options, expected):
    """Test the ``validate_stash_options`` function."""
    if expected is None:
        assert validate_stash_options(stash_options, None) is expected
    else:
        assert expected in validate_stash_options(stash_options, None)


def test_validate_monitors_valid():
    """Test the ``validate_monitors`` function for valid input."""
    monitors = {'monitor': orm.Dict({'entry_point': 'core.always_kill'})}
    result = validate_monitors(monitors, None)
    assert result is None


def test_validate_monitors_non_existent_entry_point():
    """Test the ``validate_monitors`` function for invalid entry point."""
    monitors = {'monitor': orm.Dict({'entry_point': 'not_existant_entry_point'})}
    result = validate_monitors(monitors, None)
    assert "Entry point 'not_existant_entry_point' not found in group" in result


def test_validate_monitors_invalid_signature(monkeypatch):
    """Test the ``validate_monitors`` function for existing monitor with invalid signature.

    For this test, we monkeypatch the ``BaseFactory`` which is used by the validator to load the monitor. The patched
    function will return a monitor implementation with an invalid signature.
    """
    from aiida.engine.processes.calcjobs.monitors import CalcJobMonitor

    def monitor_invalid_signature(**kwargs):
        """Monitor with invalid signature"""

    def load_entry_point(*args, **kwargs):
        return monitor_invalid_signature

    monkeypatch.setattr(CalcJobMonitor, 'load_entry_point', load_entry_point)

    monitors = {'monitor': orm.Dict({'entry_point': 'monitor_invalid_signature'})}
    result = validate_monitors(monitors, None)
    assert 'The monitor `monitor_invalid_signature` has an invalid function signature' in result


def test_validate_monitors_unsupported_kwargs():
    """Test the ``validate_monitors`` function for existing monitor receiving unsupported keyword argument."""
    monitors = {'monitor': orm.Dict({'entry_point': 'core.always_kill', 'kwargs': {'unsupported_kwarg': True}})}
    result = validate_monitors(monitors, None)
    assert 'The monitor `core.always_kill` does not accept the keywords' in result


def test_monitor_version(get_calcjob_builder):
    """Test that the version of the package of the monitors are added as attributes on the node."""
    from aiida import __version__

    builder = get_calcjob_builder()
    builder.monitors = {'monitor': orm.Dict({'entry_point': 'core.always_kill'})}
    _, node = launch.run_get_node(builder)
    assert node.base.attributes.get('version')['monitors'] == {'monitor': __version__}


def monitor_skip_parse(node, transport, **kwargs):
    """Kill the job and skip the parsing of retrieved output files."""
    return CalcJobMonitorResult(message='skip parsing', parse=False)


def test_monitor_result_parse(get_calcjob_builder, entry_points):
    """Test the ``parse`` attribute of :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult`.

    If set to ``False``, parsing of output files should be skipped.
    """
    entry_points.add(monitor_skip_parse, group='aiida.calculations.monitors', name='core.skip_parse')

    builder = get_calcjob_builder()
    builder.metadata.options.sleep = 8
    builder.monitors = {'monitor': orm.Dict({'entry_point': 'core.skip_parse'})}
    _, node = launch.run_get_node(builder)
    assert sorted(node.outputs) == ['remote_folder', 'retrieved']
    assert node.exit_status == CalcJob.exit_codes.STOPPED_BY_MONITOR.status


def monitor_skip_retrieve(node, transport, **kwargs):
    """Kill the job and skip the retrieval and parsing of retrieved output files."""
    return CalcJobMonitorResult(message='skip retrieval', retrieve=False, parse=False)


def test_monitor_result_retrieve(get_calcjob_builder, entry_points):
    """Test the ``retrieve`` attribute of :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult`.

    If set to ``False``, retrieval and parsing of output files should be skipped.
    """
    entry_points.add(monitor_skip_retrieve, group='aiida.calculations.monitors', name='core.skip_retrieval')

    builder = get_calcjob_builder()
    builder.metadata.options.sleep = 8
    builder.monitors = {'monitor': orm.Dict({'entry_point': 'core.skip_retrieval'})}
    _, node = launch.run_get_node(builder)
    assert 'retrieved' not in node.outputs
    assert node.exit_status == CalcJob.exit_codes.STOPPED_BY_MONITOR.status


def monitor_override_exit_code(node, transport, **kwargs):
    """Kill the job and do not override the exit code of the parser."""
    return CalcJobMonitorResult(message='do not override exit code', override_exit_code=False)


def test_monitor_result_override_exit_code(get_calcjob_builder, entry_points):
    """Test the ``override_exit_code`` attr of :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult`.

    If set to ``False``, parsing of output files should be skipped.
    """
    entry_points.add(monitor_override_exit_code, group='aiida.calculations.monitors', name='core.override_exit_code')

    builder = get_calcjob_builder()
    builder.metadata.options.sleep = 8
    builder.monitors = {'monitor': orm.Dict({'entry_point': 'core.override_exit_code'})}
    _, node = launch.run_get_node(builder)
    assert sorted(node.outputs) == ['remote_folder', 'retrieved']
    assert node.exit_status == ArithmeticAddCalculation.exit_codes.ERROR_INVALID_OUTPUT.status


def monitor_disable_all(node, transport, **kwargs):
    """Monitor that will disable all monitors."""
    return CalcJobMonitorResult(action=CalcJobMonitorAction.DISABLE_ALL, message='Disable all monitors.')


def test_monitor_result_action_disable_all(get_calcjob_builder, entry_points):
    """Test the ``action`` attr of :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult`.

    If set to ``CalcJobMonitorAction.DISABLE_ALL``, the calculation should continue running and no monitor should be
    invoked anymore.
    """
    entry_points.add(monitor_disable_all, group='aiida.calculations.monitors', name='core.disable_all')

    builder = get_calcjob_builder()
    builder.metadata.options.sleep = 1
    # Set priority to ensure that ``disable_all`` is run first. If the code works properly, it will be called first,
    # and so the ``always_kill`` monitor will never be called. This should cause the calculation to finish nominally.
    builder.monitors = {
        'disable_all': orm.Dict({'entry_point': 'core.disable_all', 'priority': 100}),
        'always_kill': orm.Dict({'entry_point': 'core.always_kill', 'priority': 0}),
    }
    _, node = launch.run_get_node(builder)
    assert node.is_finished_ok


def monitor_disable_self(node, transport, **kwargs):
    """Monitor that will disable itself."""
    return CalcJobMonitorResult(action=CalcJobMonitorAction.DISABLE_SELF, message='Disable self.')


@pytest.mark.usefixtures('override_logging')
def test_monitor_result_action_disable_self(get_calcjob_builder, entry_points, caplog):
    """Test the ``action`` attr of :class:`aiida.engine.processes.calcjobs.monitors.CalcJobMonitorResult`.

    If set to ``CalcJobMonitorAction.DISABLE_SELF``, the calculation should continue running and the monitor should not
    be invoked anymore, but any other monitor should continue to be called.

    The ``override_logging`` fixture is necessary to set the logging level to ``DEBUG`` because the monitor message is
    logged at the ``INFO`` level and so without this change, it would not be captured.
    """
    entry_points.add(monitor_disable_self, group='aiida.calculations.monitors', name='core.disable_self')

    builder = get_calcjob_builder()
    builder.metadata.options.sleep = 6
    builder.monitors = {'disable_self': orm.Dict({'entry_point': 'core.disable_self'})}
    _, node = launch.run_get_node(builder)
    assert node.is_finished_ok
    assert len([record for record in caplog.records if 'Disable self.' in record.message]) == 1


def test_submit_return_exit_code(get_calcjob_builder, monkeypatch):
    """Test that a job is terminated if ``Scheduler.submit_job`` returns an exit code.

    To simulate this situation we monkeypatch ``DirectScheduler._parse_submit_output`` because that is the method that
    is called internally by ``Scheduler.submit_job`` and it returns its result, and the ``DirectScheduler`` is
    the plugin that is used by the localhost computer used in the inputs for this calcjob.
    """
    from aiida.schedulers.plugins.direct import DirectScheduler

    def _parse_submit_output(self, *args):
        return ExitCode(418)

    monkeypatch.setattr(DirectScheduler, '_parse_submit_output', _parse_submit_output)

    builder = get_calcjob_builder()
    _, node = launch.run_get_node(builder)
    assert node.is_failed, (node.process_state, node.exit_status)
    assert node.exit_status == 418


@pytest.mark.requires_rmq
def test_restart_after_daemon_reset(get_calcjob_builder, daemon_client, submit_and_await):
    """Test that a job can be restarted when it is launched and the daemon is restarted.

    This is a regression test for https://github.com/aiidateam/aiida-core/issues/5882.
    """
    import time

    import plumpy

    daemon_client.start_daemon()

    # Launch a job with a one second sleep to ensure it doesn't finish before we get the chance to restart the daemon.
    # A monitor is added to ensure that those are properly reinitialized in the ``Waiting`` state of the process.
    builder = get_calcjob_builder()
    builder.metadata.options.sleep = 1
    builder.monitors = {'monitor': orm.Dict({'entry_point': 'core.always_kill', 'disabled': True})}
    node = submit_and_await(builder, plumpy.ProcessState.WAITING)

    daemon_client.restart_daemon(wait=True)

    start_time = time.time()
    timeout = 10

    while node.process_state not in [plumpy.ProcessState.FINISHED, plumpy.ProcessState.EXCEPTED]:
        if node.is_excepted:
            raise AssertionError(f'The process excepted: {node.exception}')

        if time.time() - start_time >= timeout:
            raise AssertionError(f'process failed to terminate within timeout, current state: {node.process_state}')

    assert node.is_finished, node.process_state
    assert node.is_finished_ok, node.exit_status


class TestImport:
    """Test the functionality to import existing calculations completed outside of AiiDA."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost, aiida_code_installed):
        """Initialize the profile."""
        self.computer = aiida_localhost
        self.inputs = {
            'code': aiida_code_installed(
                default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash', computer=aiida_localhost
            ),
            'x': orm.Int(1),
            'y': orm.Int(2),
            'metadata': {
                'options': {
                    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
                }
            },
        }

    def test_import_from_valid(self, tmp_path):
        """Test the import of a successfully completed `ArithmeticAddCalculation`."""
        expected_sum = (self.inputs['x'] + self.inputs['y']).value

        filepath = tmp_path / ArithmeticAddCalculation.spec_options['output_filename'].default
        with open(filepath, 'w', encoding='utf8') as handle:
            handle.write(f'{expected_sum}\n')

        remote = orm.RemoteData(str(tmp_path), computer=self.computer).store()
        inputs = deepcopy(self.inputs)
        inputs['remote_folder'] = remote

        results, node = launch.run.get_node(ArithmeticAddCalculation, **inputs)

        # Check node attributes
        assert isinstance(node, orm.CalcJobNode)
        assert node.is_finished_ok
        assert node.is_sealed
        assert node.is_imported

        # Verify the expected outputs are there
        assert 'retrieved' in results
        assert isinstance(results['retrieved'], orm.FolderData)
        assert 'sum' in results
        assert isinstance(results['sum'], orm.Int)
        assert results['sum'].value == expected_sum

    def test_import_from_invalid(self, tmp_path):
        """Test the import of a completed `ArithmeticAddCalculation` where parsing will fail.

        The `ArithmeticParser` will return a non-zero exit code if the output file could not be parsed. Make sure that
        this is piped through correctly through the infrastructure and will cause the process to be marked as failed.
        """
        filepath = tmp_path / ArithmeticAddCalculation.spec_options['output_filename'].default
        with open(filepath, 'w', encoding='utf8') as handle:
            handle.write('a\n')  # On purpose write a non-integer to output so the parsing will fail

        remote = orm.RemoteData(str(tmp_path), computer=self.computer).store()
        inputs = deepcopy(self.inputs)
        inputs['remote_folder'] = remote

        results, node = launch.run.get_node(ArithmeticAddCalculation, **inputs)

        # Check node attributes
        assert isinstance(node, orm.CalcJobNode)
        assert node.is_failed
        assert node.is_sealed
        assert node.is_imported
        assert node.exit_status == ArithmeticAddCalculation.exit_codes.ERROR_INVALID_OUTPUT.status

        # Verify the expected outputs are there
        assert 'retrieved' in results
        assert isinstance(results['retrieved'], orm.FolderData)

    def test_import_non_default_input_file(self, tmp_path):
        """Test the import of a successfully completed `ArithmeticAddCalculation`

        The only difference of this test with `test_import_from_valid` is that here the name of the output file
        of the completed calculation differs from the default written by the calculation job class.
        """
        expected_sum = (self.inputs['x'] + self.inputs['y']).value

        output_filename = 'non_standard.out'

        filepath = tmp_path / output_filename
        with open(filepath, 'w', encoding='utf8') as handle:
            handle.write(f'{expected_sum}\n')

        remote = orm.RemoteData(str(tmp_path), computer=self.computer).store()
        inputs = deepcopy(self.inputs)
        inputs['remote_folder'] = remote
        inputs['metadata']['options']['output_filename'] = output_filename

        results, node = launch.run.get_node(ArithmeticAddCalculation, **inputs)

        # Check node attributes
        assert isinstance(node, orm.CalcJobNode)
        assert node.is_finished_ok
        assert node.is_sealed
        assert node.is_imported

        # Verify the expected outputs are there
        assert 'retrieved' in results
        assert isinstance(results['retrieved'], orm.FolderData)
        assert 'sum' in results
        assert isinstance(results['sum'], orm.Int)
        assert results['sum'].value == expected_sum


@pytest.fixture
def arithmetic_add_inputs(aiida_localhost):
    return {
        'x': orm.Int(1),
        'y': orm.Int(2),
        'code': orm.InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash'),
    }


class FileCopyOperationOrderInvalid(CalcJob):
    """`Test the ``CalcInfo.file_copy_order`` attribute."""

    def prepare_for_submission(self, _):
        from aiida.common.datastructures import CalcInfo, CodeInfo

        code_info = CodeInfo()
        code_info.code_uuid = self.inputs.code.uuid
        calc_info = CalcInfo()
        calc_info.codes_info = [code_info]
        calc_info.file_copy_operation_order = [
            FileCopyOperation.REMOTE,
            'sandbox',
        ]
        return calc_info


def test_file_copy_operation_order_default(fixture_sandbox, arithmetic_add_inputs, runner):
    """Test the ``CalcInfo.file_copy_operation_order`` is set by default."""
    process = instantiate_process(runner, ArithmeticAddCalculation, **arithmetic_add_inputs)
    calc_info = process.presubmit(fixture_sandbox)
    assert calc_info.file_copy_operation_order == [
        FileCopyOperation.SANDBOX,
        FileCopyOperation.LOCAL,
        FileCopyOperation.REMOTE,
    ]


def test_file_copy_operation_order_invalid(fixture_sandbox, runner, aiida_code_installed):
    """Test the ``CalcInfo.file_copy_operation_order`` is causes exception if set to invalid type."""
    from aiida.engine.utils import instantiate_process

    inputs = {
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/true'),
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    process = instantiate_process(runner, FileCopyOperationOrderInvalid, **inputs)
    with pytest.raises(exceptions.PluginInternalError, match=r'calc_info.file_copy_operation_order is not a list .*'):
        process.presubmit(fixture_sandbox)


def test_cache_version_attribute(arithmetic_add_inputs, monkeypatch):
    """Test that the ``CalcJob.CACHE_VERSION`` and ``Parser.CACHE_VERSION`` attributes can be used to control hashes.

    If the implementation of a ``CalcJob`` or ``Parser`` plugin changes significantly, a plugin developer can change
    the ``CACHE_VERSION`` attribute to cause the hash to be changed, ensuring old completed instances of the class no
    longer to be valid cache sources.
    """
    _, node_a = launch.run_get_node(ArithmeticAddCalculation, arithmetic_add_inputs)

    monkeypatch.setattr(ArithmeticAddCalculation, 'CACHE_VERSION', 1)

    _, node_b = launch.run_get_node(ArithmeticAddCalculation, arithmetic_add_inputs)
    assert node_b.base.attributes.get(ArithmeticAddCalculation.KEY_CACHE_VERSION) == {'calc_job': 1}
    assert node_a.base.caching.get_hash() != node_b.base.caching.get_hash()
    assert not node_b.base.caching.is_created_from_cache

    monkeypatch.setattr(ArithmeticAddParser, 'CACHE_VERSION', 2)

    _, node_c = launch.run_get_node(ArithmeticAddCalculation, arithmetic_add_inputs)
    assert node_c.base.attributes.get(ArithmeticAddCalculation.KEY_CACHE_VERSION) == {
        'calc_job': 1,
        'parser': 2,
    }
    assert node_b.base.caching.get_hash() != node_c.base.caching.get_hash()
    assert not node_c.base.caching.is_created_from_cache

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for recovery around CalcJob retrieval."""

import shutil
from pathlib import Path

import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.datastructures import CalcJobState
from aiida.engine import ToContext, WorkChain, run_get_node
from aiida.engine.processes import states
from aiida.engine.processes.calcjobs import tasks
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.greenback import ensure_portal
from aiida.parsers import Parser
from aiida.plugins import TransportFactory


@pytest.mark.requires_broker
@pytest.mark.parametrize('cut', ['before_retrieval', 'after_retrieval', 'after_outputs', 'after_transition'])
def test_permanent_retrieval_checkpoint(aiida_code_installed, aiida_manager, cut):
    """Replay real checkpoints without assuming PARSING means the retrieved output was persisted."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add')
    runner = aiida_manager.get_runner()
    process = runner.instantiate_process(ArithmeticAddCalculation, code=code, x=orm.Int(1), y=orm.Int(2))

    async def replay():
        await ensure_portal()
        for _ in range(40):
            if isinstance(process._state, tasks.Waiting) and process._state._command == tasks.RETRIEVE_COMMAND:
                break
            assert not process.has_terminated()
            await process.step()
        else:
            pytest.fail('Did not reach retrieval')

        assert not process.node.get_retrieve_temporary_list()
        remote = Path(process.node.get_remote_workdir())
        assert (remote / 'aiida.out').read_text() == '3\n'
        retrieved_uuid = None

        if cut != 'before_retrieval':
            next_state = await process._state.execute()
            assert process.node.get_state() == CalcJobState.PARSING
            assert 'retrieved' not in process.node.outputs
            if cut == 'after_outputs':
                # Model loss during on_entered, after links are saved but before the checkpoint is updated.
                process.update_outputs()
            elif cut == 'after_transition':
                process.transition_to(next_state)
            if cut in ('after_outputs', 'after_transition'):
                retrieved_uuid = process.node.outputs.retrieved.uuid

        process_id = process.pid
        process.close()
        restored = runner.persister.load_checkpoint(process_id).decode()
        try:
            await restored.step_until_terminated()
            assert restored.node.is_finished_ok
            assert restored.outputs['sum'].value == 3
            retrieved = restored.node.outputs.retrieved
            assert retrieved.base.repository.get_object_content('aiida.out') == '3\n'
            assert restored.outputs['retrieved'].uuid == retrieved.uuid
            assert len(restored.node.base.links.get_outgoing(link_label_filter='retrieved').all()) == 1
            if retrieved_uuid is not None:
                assert retrieved.uuid == retrieved_uuid
            assert (remote / 'aiida.out').read_text() == '3\n'
        finally:
            restored.close()

    try:
        runner.run_until_complete(replay())
    finally:
        process.close()


class TemporaryResultCalculation(ArithmeticAddCalculation):
    """Write a numeric output retrieved only for parsing."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.inputs['metadata']['options']['parser_name'].default = 'test.temporary_result'

    def prepare_for_submission(self, folder):
        info = super().prepare_for_submission(folder)
        with folder.open(self.options.input_filename, 'a') as handle:
            handle.write("mkdir data\nprintf '123456789\\n' > data/result.txt\n")
        info.retrieve_temporary_list = ['data']
        return info


class TemporaryResultParser(Parser):
    """A numeric prefix is valid input, so a stale partial file can silently change the result."""

    def parse(self, **kwargs):
        try:
            result = int((Path(kwargs['retrieved_temporary_folder']) / 'data' / 'result.txt').read_text())
        except OSError:
            return self.exit_codes.ERROR_READING_OUTPUT_FILE
        except ValueError:
            return self.exit_codes.ERROR_INVALID_OUTPUT
        self.out('sum', orm.Int(result))


class RetrievalParentWorkChain(WorkChain):
    """Check that the complete temporary output reaches the parent workflow."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('code', valid_type=orm.Code)
        spec.output('sum', valid_type=orm.Int)
        spec.exit_code(401, 'ERROR_CHILD_FAILED', message='Calculation child failed.')
        spec.outline(cls.run_calculation, cls.inspect_calculation)

    def run_calculation(self):
        return ToContext(
            child=self.submit(TemporaryResultCalculation, code=self.inputs.code, x=orm.Int(1), y=orm.Int(2))
        )

    def inspect_calculation(self):
        if not self.ctx.child.is_finished_ok:
            return self.exit_codes.ERROR_CHILD_FAILED
        self.out('sum', self.ctx.child.outputs.sum)


@pytest.fixture
def temporary_result_parser(entry_points):
    """Register the test parser without installing a plugin."""
    entry_points.add(TemporaryResultParser, group='aiida.parsers', name='test.temporary_result')


@pytest.mark.requires_broker
@pytest.mark.parametrize('backend', ['local', 'asyncssh', 'openssh'])
@pytest.mark.parametrize('failures, partial', [(0, '123'), (1, 'invalid'), (1, '123'), (3, '123'), (20, '123')])
def test_temporary_retrieval_retries(
    aiida_localhost,
    aiida_computer_ssh,
    aiida_code_installed,
    aiida_config,
    aiida_profile,
    temporary_result_parser,
    monkeypatch,
    backend,
    failures,
    partial,
):
    """Repeated partial downloads must not reach the parser or change the parent result."""
    computer = aiida_localhost if backend == 'local' else aiida_computer_ssh(backend=backend)
    if backend != 'local':
        computer.configure(backend=backend, safe_interval=0)
    code = aiida_code_installed(computer=computer)
    aiida_config.set_option('transport.task_retry_initial_interval', 0, scope=aiida_profile.name)
    aiida_config.set_option('transport.task_maximum_attempts', failures + 1, scope=aiida_profile.name)
    aiida_config.store()
    transport_class = TransportFactory(computer.transport_type)
    original_get = transport_class.get_async
    failed_folders = []

    async def interrupted_get(self, source, destination, *args, **kwargs):
        if Path(source).name == 'data' and len(failed_folders) < failures:
            destination = Path(destination)
            destination.mkdir(exist_ok=True)
            (destination / 'result.txt').write_text(partial)
            failed_folders.append(destination.parent)
            raise OSError('injected temporary download error')
        return await original_get(self, source, destination, *args, **kwargs)

    monkeypatch.setattr(transport_class, 'get_async', interrupted_get)
    results, parent = run_get_node(RetrievalParentWorkChain, code=code)
    child = parent.base.links.get_outgoing(node_class=orm.CalcJobNode).one().node
    assert len(failed_folders) == failures
    assert parent.is_finished_ok, (parent.exit_status, child.exit_status)
    assert child.is_finished_ok
    assert results['sum'].value == 123456789
    assert child.outputs.retrieved.base.repository.get_object_content('aiida.out') == '3\n'
    assert (Path(child.get_remote_workdir()) / 'data' / 'result.txt').read_text() == '123456789\n'
    assert all(not path.exists() for path in failed_folders)


@pytest.mark.requires_broker
@pytest.mark.parametrize(
    'cut, override_status',
    [
        ('after_retrieval', 0),
        ('after_outputs', 0),
        ('after_transition', 0),
        ('after_parsing', 0),
        ('after_transition', 450),
        ('after_parsing', 450),
    ],
)
def test_temporary_retrieval_checkpoint(
    aiida_code_installed, aiida_manager, temporary_result_parser, cut, override_status
):
    """Recover temporary files even from a parsing checkpoint, preserving a requested exit-code override."""
    runner = aiida_manager.get_runner()
    process = runner.instantiate_process(
        TemporaryResultCalculation, code=aiida_code_installed(), x=orm.Int(1), y=orm.Int(2)
    )

    async def replay():
        await ensure_portal()
        for _ in range(40):
            if isinstance(process._state, tasks.Waiting) and process._state._command == tasks.RETRIEVE_COMMAND:
                break
            assert not process.has_terminated()
            await process.step()
        else:
            pytest.fail('Did not reach retrieval')

        next_state = await process._state.execute()
        folder = Path(next_state.args[0])
        assert (folder / 'data' / 'result.txt').read_text() == '123456789\n'
        retrieved_uuid = None
        if override_status:
            next_state = process._state.parse(str(folder), ExitCode(override_status, 'test override'))
        if cut == 'after_outputs':
            process.update_outputs()
        elif cut in ('after_transition', 'after_parsing'):
            process.transition_to(next_state)
        if cut != 'after_retrieval':
            retrieved_uuid = process.node.outputs.retrieved.uuid
        if cut == 'after_parsing':
            await process._state.execute()
            assert not folder.exists()
        else:
            # Model losing worker-local storage before restoring the actual saved checkpoint.
            shutil.rmtree(folder)

        process_id = process.pid
        process.close()
        restored = runner.persister.load_checkpoint(process_id).decode()
        try:
            await restored.step_until_terminated()
            assert restored.node.exit_status == override_status
            assert restored.outputs['sum'].value == 123456789
            retrieved = restored.node.outputs.retrieved
            assert retrieved.base.repository.get_object_content('aiida.out') == '3\n'
            assert restored.outputs['retrieved'].uuid == retrieved.uuid
            if retrieved_uuid is not None:
                assert retrieved.uuid == retrieved_uuid
        finally:
            restored.close()

    try:
        runner.run_until_complete(replay())
    finally:
        process.close()


@pytest.mark.requires_broker
@pytest.mark.parametrize('attempts', [1, 3])
@pytest.mark.parametrize('error_type', [OSError, states.Interruption])
def test_temporary_retrieval_resume(
    aiida_code_installed,
    aiida_manager,
    aiida_config,
    aiida_profile,
    temporary_result_parser,
    monkeypatch,
    attempts,
    error_type,
):
    """Failed or interrupted tasks clean their staging and can resume from the saved checkpoint."""
    aiida_config.set_option('transport.task_retry_initial_interval', 0, scope=aiida_profile.name)
    aiida_config.set_option('transport.task_maximum_attempts', attempts, scope=aiida_profile.name)
    aiida_config.store()
    runner = aiida_manager.get_runner()
    process = runner.instantiate_process(
        TemporaryResultCalculation, code=aiida_code_installed(), x=orm.Int(1), y=orm.Int(2)
    )
    transport_class = TransportFactory('core.local')
    original_get = transport_class.get_async
    failed_folders = []

    async def interrupted_get(self, source, destination, *args, **kwargs):
        if Path(source).name == 'data':
            destination = Path(destination)
            destination.mkdir()
            (destination / 'result.txt').write_text('123')
            failed_folders.append(destination.parent)
            raise error_type('injected download interruption')
        return await original_get(self, source, destination, *args, **kwargs)

    async def replay():
        await ensure_portal()
        for _ in range(40):
            if isinstance(process._state, tasks.Waiting) and process._state._command == tasks.RETRIEVE_COMMAND:
                break
            assert not process.has_terminated()
            await process.step()
        else:
            pytest.fail('Did not reach retrieval')

        with monkeypatch.context() as patch:
            patch.setattr(transport_class, 'get_async', interrupted_get)
            if error_type is OSError:
                await process.step()
                assert process.paused
                assert len(failed_folders) == attempts
            else:
                with pytest.raises(states.Interruption, match='injected download interruption'):
                    await process._state.execute()
                assert len(failed_folders) == 1
        assert all(not path.exists() for path in failed_folders)

        process_id = process.pid
        process.close()
        restored = runner.persister.load_checkpoint(process_id).decode()
        try:
            restored.play()
            await restored.step_until_terminated()
            assert restored.node.is_finished_ok
            assert restored.outputs['sum'].value == 123456789
        finally:
            restored.close()

    try:
        runner.run_until_complete(replay())
    finally:
        process.close()

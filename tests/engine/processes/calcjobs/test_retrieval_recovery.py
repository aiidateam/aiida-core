###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for recovery around CalcJob retrieval."""

from pathlib import Path

import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.datastructures import CalcJobState
from aiida.engine.processes.calcjobs import tasks
from aiida.engine.processes.greenback import ensure_portal


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

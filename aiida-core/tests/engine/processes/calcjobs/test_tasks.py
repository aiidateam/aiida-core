###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the transport tasks of the ``CalcJob`` process.

These tests cover the interruption, cancellation, and kill fallback paths of
the transport task coroutines and the ``Waiting`` state. These paths are only
reached incidentally during full-suite runs, so without dedicated tests their
coverage fluctuates between CI runs and shows up as Codecov indirect changes.
"""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import Mock

import pytest

from aiida.common.datastructures import CalcJobState
from aiida.common.exceptions import TransportTaskException
from aiida.engine.processes import states
from aiida.engine.processes.calcjobs import tasks


def _config(option):
    """Return a fixed value for the configuration options read by the transport tasks."""
    return {
        tasks.RETRY_INTERVAL_OPTION: 0,
        tasks.MAX_ATTEMPTS_OPTION: 2,
        'storage.sandbox': None,
    }[option]


class _InterruptingCancellable:
    """A cancellable whose ``with_interrupt`` immediately raises an interruption."""

    async def with_interrupt(self, request):
        raise states.Interruption('interrupted')


class _PassthroughCancellable:
    """A cancellable that returns the request unchanged."""

    async def with_interrupt(self, request):
        return request


class TestTransportTasks:
    """Unit tests for the calcjob transport task coroutines."""

    @pytest.mark.asyncio
    async def test_submit_job_reraises_transport_task_exception(self, monkeypatch):
        """Exhausted submit retries raise a ``TransportTaskException``."""
        monkeypatch.setattr(tasks, 'get_config_option', _config)
        monkeypatch.setattr(tasks.execmanager, 'submit_calculation', Mock(side_effect=RuntimeError('no connection')))

        node = Mock()
        node.get_authinfo.return_value = Mock()

        @asynccontextmanager
        async def request_transport(authinfo):
            yield Mock()

        transport_queue = Mock()
        transport_queue.request_transport = request_transport

        with pytest.raises(TransportTaskException, match='failed 2 times consecutively'):
            await tasks.task_submit_job(node, transport_queue, _PassthroughCancellable())

    @pytest.mark.asyncio
    async def test_upload_job_reraises_interruption(self, monkeypatch):
        """An interruption while uploading is re-raised and not retried."""
        monkeypatch.setattr(tasks, 'get_config_option', _config)

        node = Mock()
        node.get_state.return_value = CalcJobState.UPLOADING
        node.get_authinfo.return_value = Mock()

        process = Mock()
        process.node = node

        @asynccontextmanager
        async def request_transport(authinfo):
            yield Mock()

        transport_queue = Mock()
        transport_queue.request_transport = request_transport

        with pytest.raises(states.Interruption):
            await tasks.task_upload_job(process, transport_queue, _InterruptingCancellable())

    @pytest.mark.asyncio
    async def test_update_job_reraises_interruption(self, monkeypatch):
        """An interruption while updating the scheduler state is re-raised and not retried."""
        monkeypatch.setattr(tasks, 'get_config_option', _config)

        node = Mock()
        node.get_state.return_value = CalcJobState.PARSING
        node.get_authinfo.return_value = Mock()
        node.get_job_id.return_value = 'job-id'

        @contextmanager
        def request_job_info_update(authinfo, job_id):
            yield Mock()

        job_manager = Mock()
        job_manager.request_job_info_update = request_job_info_update

        with pytest.raises(states.Interruption):
            await tasks.task_update_job(node, job_manager, _InterruptingCancellable())


class TestWaiting:
    """Unit tests for the calcjob ``Waiting`` state's interruption handling."""

    def _make_waiting(self, data=None):
        process = Mock()
        process.loop = asyncio.get_running_loop()
        process.node = Mock()
        process.runner = Mock()
        return tasks.Waiting(process, done_callback=None, data=data)

    @pytest.mark.asyncio
    async def test_interrupt_kill_creates_killing_future(self):
        """Interrupting with a kill creates and returns a single killing future."""
        waiting = self._make_waiting()
        assert waiting._killing is None

        killing = waiting.interrupt(states.KillInterruption('kill'))
        assert killing is waiting._killing
        assert not killing.done()

        # A subsequent kill interruption reuses the same future
        assert waiting.interrupt(states.KillInterruption('kill')) is killing

    @pytest.mark.asyncio
    async def test_execute_finally_resolves_killing_future(self):
        """The execute finally block resolves an unresolved killing future."""
        waiting = self._make_waiting(data={'command': 'bogus'})
        waiting.interrupt(states.KillInterruption('kill'))

        with pytest.raises(RuntimeError, match='Unknown waiting command'):
            await waiting.execute()

        assert waiting._killing.done()

    @pytest.mark.asyncio
    async def test_execute_kill_interruption_retrieves(self, monkeypatch):
        """A kill interruption during a transport task records it and retrieves the job."""

        async def fake_submit_job(node, transport_queue, cancellable):
            raise states.KillInterruption('kill')

        monkeypatch.setattr(tasks, 'task_submit_job', fake_submit_job)

        waiting = self._make_waiting(data={'command': tasks.SUBMIT_COMMAND})
        waiting.process.create_state.return_value = 'retrieved-state'

        result = await waiting.execute()

        waiting.process.node.set_process_status.assert_any_call('kill')
        assert result == 'retrieved-state'

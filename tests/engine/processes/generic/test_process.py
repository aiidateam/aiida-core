"""Tests for internal process futures."""

import asyncio
from unittest.mock import Mock

import pytest

from aiida.engine.processes.generic.process import Process
from aiida.engine.processes.states import KillInterruption, PauseInterruption


@pytest.mark.parametrize('interruption', [PauseInterruption(None), KillInterruption(None)])
def test_interrupt_action_uses_process_loop(interruption):
    """Test pause and kill actions bind to the process event loop."""
    loop = asyncio.new_event_loop()
    process = Mock(loop=loop)

    try:
        action = Process._create_interrupt_action(process, interruption)

        assert action.get_loop() is loop
    finally:
        loop.close()

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapter module for optional aiida-workgraph integration.

This module provides a centralized location for checking availability
of aiida-workgraph components. It allows aiida-core to optionally support WorkGraph
processes without requiring aiida-workgraph as a dependency.

Usage:
    from aiida.common.workgraph import WORKGRAPH_AVAILABLE, is_workgraph_instance

    if is_workgraph_instance(process):
        # WorkGraph-specific code
        ...
"""

# mypy: disable-error-code="unused-ignore"
# aiida-workgraph is an optional dependency: mypy raises import-not-found when
# it is absent and import-untyped when it is present.  Both codes are needed in
# type-ignore comments, but one will always be unused, so we suppress that check.
from __future__ import annotations

import typing as t

from aiida.common.exceptions import InvalidOperation
from aiida.common.log import AIIDA_LOGGER
from aiida.engine.utils import prepare_inputs

# Check if aiida-workgraph is available
try:
    import aiida_workgraph  # type: ignore[import-not-found,import-untyped]  # noqa: F401

    WORKGRAPH_AVAILABLE = True
except ImportError:
    WORKGRAPH_AVAILABLE = False


LOGGER = AIIDA_LOGGER.getChild('engine.launch')

_KEY_METADATA = 'metadata'
_KEY_TIMEOUT = 'timeout'
_KEY_DRY_RUN = 'dry_run'
_KEY_WAIT = 'wait'
_KEY_INTERVAL = 'interval'

_WORKGRAPH_RUN_RESERVED_KEYS = {_KEY_METADATA}
_WORKGRAPH_SUBMIT_RESERVED_KEYS = {_KEY_METADATA, _KEY_TIMEOUT, _KEY_WAIT, _KEY_INTERVAL}


def is_workgraph_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraph instance.

    Returns False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraph instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph import WorkGraph  # type: ignore[import-not-found,import-untyped]

    return isinstance(obj, WorkGraph)


def _prepare_workgraph_inputs(
    workgraph: t.Any,
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
    reserved_keys: set[str],
) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
    """Merge and validate inputs for a WorkGraph launch, popping reserved keys.

    :param workgraph: the WorkGraph instance
    :param inputs: the input dictionary
    :param kwargs: additional keyword arguments to be merged with inputs
    :param reserved_keys: set of keys to pop from inputs and return separately
    :raises ValueError: if both ``inputs`` and ``kwargs`` are specified
    :raises InvalidOperation: if reserved keys collide with task names
    :return: tuple of (task inputs, popped reserved key values)
    """
    wg_inputs = prepare_inputs(inputs, **kwargs).copy()  # copy: reserved keys are popped below
    popped: dict[str, t.Any] = {}
    for key in reserved_keys:
        value = wg_inputs.pop(key, None)
        if value is not None:
            popped[key] = value

    collisions = set(popped) & set(workgraph.get_task_names())
    if collisions:
        raise InvalidOperation(
            f'Keys {collisions} are reserved execution parameters but also match task names '
            f'on this WorkGraph. Rename the tasks to avoid colliding with reserved keys: {reserved_keys}.'
        )

    return wg_inputs, popped


def engine_run_workgraph(
    workgraph: t.Any,
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
) -> tuple[dict[str, t.Any], t.Any]:
    """Run a WorkGraph locally, returning its outputs and process node.

    Inlines the logic of ``WorkGraph.run()`` so that aiida-core owns the launch path.

    :param workgraph: the WorkGraph instance
    :param inputs: the input dictionary (task name -> value)
    :param kwargs: alternative to ``inputs``
    :raises ValueError: if both ``inputs`` and ``kwargs`` are specified
    :return: tuple of the outputs and the process node
    """
    from aiida.engine.launch import run_get_node

    wg_inputs, popped = _prepare_workgraph_inputs(
        workgraph=workgraph, inputs=inputs, kwargs=kwargs, reserved_keys=_WORKGRAPH_RUN_RESERVED_KEYS
    )

    if wg_inputs:
        workgraph.set_inputs(wg_inputs)
    workgraph.check_before_run()

    from aiida_workgraph.engine.workgraph import WorkGraphEngine  # type: ignore[import-not-found,import-untyped]

    engine_inputs = workgraph.to_engine_inputs(metadata=popped.get(_KEY_METADATA))
    _, node = run_get_node(WorkGraphEngine, inputs=engine_inputs)
    workgraph.process = node
    workgraph.update()
    return workgraph.outputs._value, node


def engine_submit_workgraph(
    workgraph: t.Any,
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
    *,
    wait: bool,
    wait_interval: int,
) -> t.Any:
    """Submit a WorkGraph to the daemon, returning its process node.

    Inlines the logic of ``WorkGraph.save()`` + ``WorkGraph.continue_process()``
    so that aiida-core owns the launch path.

    :param workgraph: the WorkGraph instance
    :param inputs: the input dictionary (task name -> value)
    :param kwargs: alternative to ``inputs``
    :param wait: whether to block until the process completes
    :param wait_interval: seconds between status checks when ``wait=True``
    :raises ValueError: if both ``inputs`` and ``kwargs`` are specified
    :raises InvalidOperation: if ``dry_run`` is requested (not supported by WorkGraph)
    :return: the process node
    """
    import time

    from aiida.engine.utils import instantiate_process
    from aiida.manage import manager

    wg_inputs, popped = _prepare_workgraph_inputs(
        workgraph=workgraph, inputs=inputs, kwargs=kwargs, reserved_keys=_WORKGRAPH_SUBMIT_RESERVED_KEYS
    )
    metadata = popped.get(_KEY_METADATA)
    timeout = popped.get(_KEY_TIMEOUT)
    wait = popped.get(_KEY_WAIT, wait)
    wait_interval = popped.get(_KEY_INTERVAL, wait_interval)

    if metadata and metadata.get(_KEY_DRY_RUN, False):
        raise InvalidOperation('WorkGraph does not support `dry_run`.')

    if wg_inputs:
        workgraph.set_inputs(wg_inputs)

    # save() logic: check, build engine inputs, instantiate & persist
    workgraph.check_before_run()
    engine_inputs = workgraph.to_engine_inputs(metadata=metadata)

    from aiida_workgraph.engine.workgraph import WorkGraphEngine  # type: ignore[import-not-found,import-untyped]

    runner = manager.get_manager().get_runner()
    process_inited = instantiate_process(runner, WorkGraphEngine, **engine_inputs)
    if process_inited.runner.persister is None:
        raise InvalidOperation('Cannot submit because the runner does not have a persister.')
    process_inited.runner.persister.save_checkpoint(process_inited)
    workgraph.process = process_inited.node
    process_inited.close()
    LOGGER.report('WorkGraph process created, PK: %s', workgraph.process.pk)

    # continue_process(): tell the daemon to pick it up
    process_controller = manager.get_manager().get_process_controller()
    process_controller.continue_process(workgraph.pk)
    workgraph.restart_process = None
    workgraph.update()

    node = workgraph.process
    if not wait:
        return node

    # Wait loop with optional timeout
    start_time = time.time()
    while not node.is_terminated:
        if timeout is not None and (time.time() - start_time) > timeout:
            raise TimeoutError(f'WorkGraph process<{node.pk}> did not finish within {timeout} seconds.')
        LOGGER.report(
            f'Process<{node.pk}> has not yet terminated, current state is `{node.process_state}`. '
            f'Waiting for {wait_interval} seconds.'
        )
        time.sleep(wait_interval)

    return node

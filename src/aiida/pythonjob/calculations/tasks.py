from __future__ import annotations

import asyncio
import functools
import logging
import traceback
from typing import Any, Callable, Optional

from aiida.engine.processes import persistence, states
from aiida.engine.processes.generic import futures
from aiida.engine.processes.process import Process, ProcessState
from aiida.engine.utils import InterruptableFuture, interruptable_task
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.utils.struct_utils import coerce_inputs_from_spec

from aiida.pythonjob.calculations.common import ATTR_DESERIALIZERS, ATTR_INPUTS_SPEC
from aiida.pythonjob.data.deserializer import deserialize_to_raw_python_data

logger = logging.getLogger(__name__)


async def monitor(function, interval, timeout, *args, **kwargs):
    """Monitor the function until it returns `True` or the timeout is reached."""
    import time

    start_time = time.time()
    while True:
        if asyncio.iscoroutinefunction(function):
            result = await function(*args, **kwargs)
        else:
            result = function(*args, **kwargs)
        if result:
            break
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Function monitoring timed out after {timeout} seconds")
        await asyncio.sleep(interval)


async def task_run_job(process: Process, *args, **kwargs) -> Any:
    """Run the *async* user function and return results or a structured error."""
    node = process.node

    inputs = dict(process.inputs.function_inputs or {})
    deserializers = node.base.attributes.get(ATTR_DESERIALIZERS, {})
    inputs = deserialize_to_raw_python_data(inputs, deserializers=deserializers)
    inputs_spec = node.base.attributes.get(ATTR_INPUTS_SPEC, {})
    if inputs_spec:
        inputs = coerce_inputs_from_spec(inputs, SocketSpec.from_dict(inputs_spec))

    try:
        logger.info(f"scheduled request to run the function<{node.pk}>")
        results = await process.func(**inputs)  # async user function
        logger.info(f"running function<{node.pk}> successful")
        return {"__ok__": True, "results": results}
    except Exception as exception:
        logger.warning(f"running function<{node.pk}> failed")
        return {
            "__error__": "ERROR_FUNCTION_EXECUTION_FAILED",
            "exception": str(exception),
            "traceback": traceback.format_exc(),
        }


async def task_run_monitor_job(process: Process, *args, **kwargs) -> Any:
    """Run the *async* user function and return results or a structured error."""
    node = process.node

    inputs = dict(process.inputs.function_inputs or {})
    deserializers = node.base.attributes.get(ATTR_DESERIALIZERS, {})
    inputs = deserialize_to_raw_python_data(inputs, deserializers=deserializers)
    inputs_spec = node.base.attributes.get(ATTR_INPUTS_SPEC, {})
    if inputs_spec:
        inputs = coerce_inputs_from_spec(inputs, SocketSpec.from_dict(inputs_spec))

    try:
        logger.info(f"scheduled request to run the function<{node.pk}>")
        results = await monitor(process.func, interval=process.inputs.interval, timeout=process.inputs.timeout, **inputs)
        logger.info(f"running function<{node.pk}> successful")
        return {"__ok__": True, "results": results}
    except TimeoutError as exception:
        logger.warning(f"running function<{node.pk}> timed out")
        return {
            "__error__": "ERROR_TIMEOUT",
            "exception": str(exception),
            "traceback": traceback.format_exc(),
        }
    except Exception as exception:
        logger.warning(f"running function<{node.pk}> failed")
        return {
            "__error__": "ERROR_FUNCTION_EXECUTION_FAILED",
            "exception": str(exception),
            "traceback": traceback.format_exc(),
        }


@persistence.auto_persist("msg", "data")
class Waiting(states.Waiting):
    """The waiting state for the `PyFunction` process."""

    task_run_job = staticmethod(task_run_job)

    def __init__(
        self,
        process: Process,
        done_callback: Optional[Callable[..., Any]],
        msg: Optional[str] = None,
        data: Optional[Any] = None,
    ):
        super().__init__(process, done_callback, msg, data)
        self._task: InterruptableFuture | None = None
        self._killing: futures.Future | None = None

    @property
    def process(self) -> Process:
        return self.state_machine

    def load_instance_state(self, saved_state, load_context):
        super().load_instance_state(saved_state, load_context)
        self._task = None
        self._killing = None

    async def execute(self) -> states.State:
        node = self.process.node
        node.set_process_status("Running async function")
        try:
            payload = await self._launch_task(self.task_run_job, self.process)

            # Convert structured payloads into the next state or an ExitCode
            if payload.get("__ok__"):
                return self.parse(payload["results"])
            elif payload.get("__error__"):
                err = payload["__error__"]
                exit_code = getattr(self.process.exit_codes, err).format(
                    exception=payload.get("exception", ""),
                    traceback=payload.get("traceback", ""),
                )
                # Jump straight to FINISHED by scheduling parse with the error ExitCode
                # We reuse the Running->parse path so the process finishes uniformly.
                return self.create_state(ProcessState.RUNNING, self.process.parse, {"__exit_code__": exit_code})
        except states.KillInterruption as exception:
            node.set_process_status(str(exception))
            raise
        except (futures.CancelledError, asyncio.CancelledError):
            node.set_process_status('Function task "run" was cancelled')
            raise
        except states.Interruption:
            node.set_process_status('Function task "run" was interrupted')
            raise
        finally:
            node.set_process_status(None)
            if self._killing and not self._killing.done():
                self._killing.set_result(False)

    async def _launch_task(self, coro, *args, **kwargs):
        """Launch a coroutine as a task, making sure it is interruptable."""
        task_fn = functools.partial(coro, *args, **kwargs)
        try:
            self._task = interruptable_task(task_fn)
            return await self._task
        finally:
            self._task = None

    def parse(self, results: dict) -> states.Running:
        """Advance to RUNNING where the process' `parse` will be called with results."""
        return self.create_state(ProcessState.RUNNING, self.process.parse, results)

    def interrupt(self, reason: Any) -> Optional[futures.Future]:  # type: ignore[override]
        if self._task is not None:
            self._task.interrupt(reason)
        if isinstance(reason, states.KillInterruption):
            if self._killing is None:
                self._killing = futures.Future()
            return self._killing
        return None


class MonitorWaiting(Waiting):
    """A version of Waiting that can be monitored."""

    task_run_job = staticmethod(task_run_monitor_job)

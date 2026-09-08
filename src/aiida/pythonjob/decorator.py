from __future__ import annotations

import functools
import logging
import signal
import sys
import typing as t
from typing import List

import aiida
from aiida.engine.processes.functions import FunctionType
from aiida.manage import get_manager
from aiida.orm import ProcessNode
from aiida.node_graph.socket_spec import SocketSpec
from packaging.version import parse as parse_version

from aiida.pythonjob.calculations.pyfunction import PyFunction
from aiida.pythonjob.launch import create_inputs, prepare_pyfunction_inputs

LOGGER = logging.getLogger(__name__)

_AIIDA_VERSION = parse_version(aiida.__version__)
_NEEDS_RECURSION_LIMIT_WORKAROUND = _AIIDA_VERSION < parse_version("2.8.0rc0")

if _NEEDS_RECURSION_LIMIT_WORKAROUND:
    from aiida.engine.processes.functions import get_stack_size


# The following code is modified from the aiida-core.engine.processes.functions module
def pyfunction(
    inputs: t.Optional[SocketSpec | List[str]] = None,
    outputs: t.Optional[t.List[SocketSpec | List[str]]] = None,
) -> t.Callable[[FunctionType], FunctionType]:
    """The base function decorator to create a FunctionProcess out of a normal python function.

    :param outputs: the outputs of the function, if not provided, we assume a single output named 'result'.
    """

    def decorator(function: FunctionType) -> FunctionType:
        """Turn the decorated function into a FunctionProcess.

        :param callable function: the actual decorated function that the FunctionProcess represents
        :return callable: The decorated function.
        """

        def run_get_node(*args, **kwargs) -> tuple[dict[str, t.Any] | None, "ProcessNode"]:
            """Run the FunctionProcess with the supplied inputs in a local runner.

            :param args: input arguments to construct the FunctionProcess
            :param kwargs: input keyword arguments to construct the FunctionProcess
            :return: tuple of the outputs of the process and the process node
            """
            if _NEEDS_RECURSION_LIMIT_WORKAROUND:
                frame_delta = 1000
                frame_count = get_stack_size()
                stack_limit = sys.getrecursionlimit()
                LOGGER.info(
                    "Executing process function, current stack status: %d frames of %d", frame_count, stack_limit
                )

                if frame_count > min(0.8 * stack_limit, stack_limit - 200):
                    LOGGER.warning(
                        "Current stack contains %d frames which is close to the limit of %d. Increasing the limit by %d",
                        frame_count,
                        stack_limit,
                        frame_delta,
                    )
                    sys.setrecursionlimit(stack_limit + frame_delta)

            manager = get_manager()
            runner = manager.get_runner()
            # Remove all the known inputs from the kwargs
            outputs_spec = kwargs.pop("outputs_spec", None) or outputs
            inputs_spec = kwargs.pop("inputs_spec", None) or inputs
            metadata = kwargs.pop("metadata", None)
            function_data = kwargs.pop("function_data", None)
            deserializers = kwargs.pop("deserializers", None)
            serializers = kwargs.pop("serializers", None)
            process_label = kwargs.pop("process_label", None)
            register_pickle_by_value = kwargs.pop("register_pickle_by_value", False)

            function_inputs = create_inputs(function, *args, **kwargs)
            process_inputs = prepare_pyfunction_inputs(
                function=function,
                function_inputs=function_inputs,
                inputs_spec=inputs_spec,
                outputs_spec=outputs_spec,
                metadata=metadata,
                process_label=process_label,
                function_data=function_data,
                deserializers=deserializers,
                serializers=serializers,
                register_pickle_by_value=register_pickle_by_value,
            )

            process = PyFunction(inputs=process_inputs, runner=runner)

            # Only add handlers for interrupt signal to kill the process if we are in a local and not a daemon runner.
            # Without this check, running process functions in a daemon worker would be killed if the daemon is shutdown
            current_runner = manager.get_runner()
            original_handler = None
            kill_signal = signal.SIGINT

            if not current_runner.is_daemon_runner:

                def kill_process(_num, _frame):
                    """Send the kill signal to the process in the current scope."""
                    LOGGER.critical("runner received interrupt, killing process %s", process.pid)
                    result = process.kill(msg="Process was killed because the runner received an interrupt")
                    return result

                # Store the current handler on the signal such that it can be restored after process has terminated
                original_handler = signal.getsignal(kill_signal)
                signal.signal(kill_signal, kill_process)

            try:
                result = process.execute()
            finally:
                # If the `original_handler` is set, that means the `kill_process` was bound, which needs to be reset
                if original_handler:
                    signal.signal(signal.SIGINT, original_handler)

            store_provenance = process_inputs.get("metadata", {}).get("store_provenance", True)
            if not store_provenance:
                process.node._storable = False
                process.node._unstorable_message = "cannot store node because it was run with `store_provenance=False`"

            return result, process.node

        def run_get_pk(*args, **kwargs) -> tuple[dict[str, t.Any] | None, int]:
            """Recreate the `run_get_pk` utility launcher.

            :param args: input arguments to construct the FunctionProcess
            :param kwargs: input keyword arguments to construct the FunctionProcess
            :return: tuple of the outputs of the process and the process node pk

            """
            result, node = run_get_node(*args, **kwargs)
            assert node.pk is not None
            return result, node.pk

        @functools.wraps(function)
        def decorated_function(*args, **kwargs):
            """This wrapper function is the actual function that is called."""
            result, _ = run_get_node(*args, **kwargs)
            return result

        decorated_function.func = function  # type: ignore[attr-defined]
        decorated_function.run = decorated_function  # type: ignore[attr-defined]
        decorated_function.run_get_pk = run_get_pk  # type: ignore[attr-defined]
        decorated_function.run_get_node = run_get_node  # type: ignore[attr-defined]
        decorated_function.is_process_function = True  # type: ignore[attr-defined]
        decorated_function.process_class = PyFunction  # type: ignore[attr-defined]
        decorated_function.recreate_from = PyFunction.recreate_from  # type: ignore[attr-defined]
        decorated_function.spec = PyFunction.spec  # type: ignore[attr-defined]

        return decorated_function  # type: ignore[return-value]

    return decorator

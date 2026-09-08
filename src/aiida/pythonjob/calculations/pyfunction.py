"""Proess to run a Python function locally"""

from __future__ import annotations

import asyncio
import traceback
import typing as t

import cloudpickle
from aiida.engine.processes import persistence, states
from aiida.common.lang import override
from aiida.engine import Process, ProcessSpec, ProcessState
from aiida.engine.processes.exit_code import ExitCode
from aiida.orm import CalcFunctionNode, Float
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.utils.struct_utils import coerce_inputs_from_spec

from aiida.pythonjob.calculations.common import (
    ATTR_DESERIALIZERS,
    ATTR_INPUTS_SPEC,
    ATTR_OUTPUTS_SPEC,
    ATTR_SERIALIZERS,
    FunctionProcessMixin,
    add_common_function_io,
)
from aiida.pythonjob.data.deserializer import deserialize_to_raw_python_data
from aiida.pythonjob.parsers.utils import parse_outputs

from .tasks import MonitorWaiting, Waiting

__all__ = ("PyFunction",)


class PyFunction(FunctionProcessMixin, Process):
    _node_class = CalcFunctionNode
    label_template = "{name}"
    default_name = "anonymous_function"
    _WAITING = Waiting

    def __init__(self, *args, **kwargs) -> None:
        if kwargs.get("enable_persistence", False):
            raise RuntimeError("Cannot persist a function process")
        super().__init__(enable_persistence=False, *args, **kwargs)  # type: ignore[misc]
        self._func = None

    @override
    def load_instance_state(
        self, saved_state: t.MutableMapping[str, t.Any], load_context: persistence.CheckpointContext
    ) -> None:
        """Load the instance state (restore pickled function)."""
        super().load_instance_state(saved_state, load_context)
        self._func = cloudpickle.loads(self.inputs.function_data.pickled_function)

    @property
    def func(self) -> t.Callable[..., t.Any]:
        if self._func is None:
            self._func = cloudpickle.loads(self.inputs.function_data.pickled_function)
        return self._func

    def _extract_declared_name(self) -> str | None:
        name = super()._extract_declared_name()
        if name:
            return name
        try:
            return self.func.__name__
        except Exception:
            return None

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        """Define inputs/outputs and exit codes."""
        super().define(spec)
        add_common_function_io(spec)
        spec.inputs.dynamic = True
        spec.outputs.dynamic = True
        spec.exit_code(
            323,
            "ERROR_FUNCTION_EXECUTION_FAILED",
            invalidates_cache=True,
            message="Function execution failed.\n{exception}\n{traceback}",
        )

    @classmethod
    def get_state_classes(cls) -> t.Dict[t.Hashable, t.Type[states.State]]:
        states_map = super().get_state_classes()
        states_map[ProcessState.WAITING] = cls._WAITING
        return states_map

    @override
    def _setup_db_record(self) -> None:
        super()._setup_db_record()
        self.node.store_source_info(self.func)

    def execute(self) -> dict[str, t.Any] | None:
        """Mirror calcfunction behavior: unwrap single-output dicts to a bare value."""
        result = super().execute()
        if result and len(result) == 1 and self.SINGLE_OUTPUT_LINKNAME in result:
            return result[self.SINGLE_OUTPUT_LINKNAME]
        return result

    @override
    async def run(self) -> t.Union[states.Stop, int, states.Wait]:
        if self.node.exit_status is not None:
            return ExitCode(self.node.exit_status, self.node.exit_message)

        func = self.func

        # Async user function -> schedule via Waiting (interruptable)
        if asyncio.iscoroutinefunction(func):
            return states.Wait(msg="Waiting to run")

        # Sync user function -> execute now, parse outputs, and finish
        try:
            inputs = dict(self.inputs.function_inputs or {})
            deserializers = self.node.base.attributes.get(ATTR_DESERIALIZERS, {})
            inputs = deserialize_to_raw_python_data(inputs, deserializers=deserializers)
            inputs_spec = self.node.base.attributes.get(ATTR_INPUTS_SPEC, {})
            if inputs_spec:
                inputs = coerce_inputs_from_spec(inputs, SocketSpec.from_dict(inputs_spec))
        except Exception as exception:
            return self.exit_codes.ERROR_DESERIALIZE_INPUTS_FAILED.format(
                exception=str(exception), traceback=traceback.format_exc()
            )

        try:
            results = self.func(**inputs)
        except Exception as exception:
            return self.exit_codes.ERROR_FUNCTION_EXECUTION_FAILED.format(
                exception=str(exception), traceback=traceback.format_exc()
            )

        return self.parse(results)

    def parse(self, results: t.Optional[dict] = None) -> ExitCode:
        """Parse and attach outputs, or short-circuit with a provided ExitCode."""
        # Short-circuit: Waiting handed us a pre-built ExitCode
        if isinstance(results, dict) and "__exit_code__" in results:
            return results["__exit_code__"]

        outputs_spec = SocketSpec.from_dict(self.node.base.attributes.get(ATTR_OUTPUTS_SPEC) or {})
        serializers = self.node.base.attributes.get(ATTR_SERIALIZERS, {})

        outputs, exit_code = parse_outputs(
            results,
            output_spec=outputs_spec,
            exit_codes=self.exit_codes,
            logger=self.logger,
            serializers=serializers,
        )
        if exit_code:
            return exit_code

        for name, value in (outputs or {}).items():
            self.out(name, value)
        return ExitCode()


class MonitorPyFunction(PyFunction):
    """A version of PyFunction that can be monitored."""

    default_name = "monitor_function"
    _WAITING = MonitorWaiting

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        """Define inputs/outputs and exit codes."""
        super().define(spec)
        spec.input(
            "interval",
            valid_type=Float,
            default=lambda: Float(5.0),
            serializer=to_aiida_type,
            help="Polling interval in seconds.",
        )
        spec.input(
            "timeout",
            valid_type=Float,
            default=lambda: Float(3600.0),
            serializer=to_aiida_type,
            help="Timeout in seconds.",
        )

        spec.exit_code(
            324,
            "ERROR_TIMEOUT",
            invalidates_cache=True,
            message="Monitor function execution timed out.\n{exception}\n{traceback}",
        )

    @override
    async def run(self) -> t.Union[states.Stop, int, states.Wait]:
        if self.node.exit_status is not None:
            return ExitCode(self.node.exit_status, self.node.exit_message)

        return states.Wait(msg="Waiting to run")

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Declaration of a task: what it runs, and the ports it takes and produces."""

from __future__ import annotations

import collections.abc
import typing as t
from dataclasses import dataclass

from aiida.common.lang import override
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.functions import FunctionProcess, ProcessFunctionType, process_function
from aiida.engine.processes.generic.ports import PortNamespace
from aiida.engine.processes.process import Process
from aiida.orm import CalcFunctionNode, Data
from aiida.orm.nodes.data.base import to_aiida_type

__all__ = ('ExecutorReference', 'TaskProcess', 'TaskSpec', 'task')

P = t.ParamSpec('P')
R_co = t.TypeVar('R_co', covariant=True)

SPEC_VERSION: str = '1.0'
"""Version of the task declaration format, stored with every serialized spec."""


@dataclass(frozen=True)
class ExecutorReference:
    """Importable reference to the process that realizes a task.

    The reference is stored instead of the process class itself, so that a declaration can be written to the
    database and read back. A process function is referenced through the decorated function, since that is the
    importable name; the generated process class is recovered from it on load.
    """

    module: str
    name: str

    @classmethod
    def from_process(cls, process: t.Any) -> ExecutorReference:
        """Return the reference for a process class or a decorated process function.

        The name is recorded without checking that it can be imported, so that a task defined next to the code
        that runs it stays usable. Whether it truly is importable only matters once the reference is loaded, which
        is where a daemon worker would need it anyway.

        :param process: the process class or process function to reference.
        :raises ValueError: if the process carries no module and name to reference it by.
        """
        module = getattr(process, '__module__', None)
        name = getattr(process, '__name__', None)

        if module is None or name is None:
            raise ValueError(f'`{process}` cannot be referenced because it has no module and name.')

        return cls(module=module, name=name)

    def load(self) -> type[Process]:
        """Return the process class this reference points to."""
        loaded = get_object_loader().load_object(f'{self.module}:{self.name}')

        # A process function's name resolves to the decorated function, which carries the generated process class.
        if getattr(loaded, 'is_process_function', False):
            return loaded.process_class

        return loaded

    def to_dict(self) -> dict[str, str]:
        return {'module': self.module, 'name': self.name}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> ExecutorReference:
        return cls(module=data['module'], name=data['name'])


@dataclass(frozen=True)
class TaskSpec:
    """Declarative description of a task.

    A task declares what should run, without running anything itself. The ports it takes and produces are those of
    the process that realizes it, so they are derived from the executor rather than stored alongside it, which
    keeps the declaration a small value that can be written to the database and read back.
    """

    identifier: str
    executor: ExecutorReference
    version: str = SPEC_VERSION

    @classmethod
    def from_process(cls, process: t.Any, identifier: str | None = None) -> TaskSpec:
        """Return the declaration of a task that runs the given process.

        :param process: the process class or process function that realizes the task.
        :param identifier: name of the task, which defaults to the name of the process.
        """
        reference = ExecutorReference.from_process(process)
        return cls(identifier=identifier or reference.name, executor=reference)

    @property
    def process_class(self) -> type[Process]:
        """Return the process that realizes this task."""
        return self.executor.load()

    @property
    def inputs(self) -> PortNamespace:
        """Return the input ports this task takes."""
        return self.process_class.spec().inputs

    @property
    def outputs(self) -> PortNamespace:
        """Return the output ports this task produces."""
        return self.process_class.spec().outputs

    def get_builder(self) -> ProcessBuilder:
        """Return a builder with which to populate the inputs of this task."""
        return self.process_class.get_builder()

    def to_dict(self) -> dict[str, t.Any]:
        return {'identifier': self.identifier, 'executor': self.executor.to_dict(), 'version': self.version}

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> TaskSpec:
        return cls(
            identifier=data['identifier'],
            executor=ExecutorReference.from_dict(data['executor']),
            version=data.get('version', SPEC_VERSION),
        )


class TaskProcess(FunctionProcess):
    """A :class:`FunctionProcess` whose wrapped function takes and returns plain Python values.

    Values that are not already a ``Data`` node are serialized with ``to_aiida_type``, mirroring the serialization
    that the input ports of a function process already perform. When the task declares its output ports, a returned
    tuple is mapped onto them in order.
    """

    @override
    def _out_result(self, result: t.Any) -> None:
        declared = list(self.spec().outputs.keys())

        if not self.spec().outputs.dynamic and not isinstance(result, collections.abc.Mapping):
            values = result if isinstance(result, tuple) else (result,)

            if len(values) != len(declared):
                raise ValueError(
                    f'`{self.process_class.__name__}` declares {len(declared)} outputs {declared} but the function '
                    f'returned {len(values)} value(s).'
                )

            result = dict(zip(declared, values, strict=True))

        if isinstance(result, collections.abc.Mapping):
            result = {key: value if isinstance(value, Data) else to_aiida_type(value) for key, value in result.items()}
        elif not isinstance(result, Data):
            result = to_aiida_type(result)

        super()._out_result(result)


def task(
    function: t.Callable[P, R_co] | None = None,
    *,
    outputs: t.Sequence[str] | None = None,
    identifier: str | None = None,
) -> t.Any:
    """Declare a standard python function as a task.

    A task records its execution like a :func:`~aiida.engine.processes.functions.calcfunction` does, and
    additionally takes and returns plain Python values. It can be launched on its own, including by a running
    process that dispatches it as a called child, as long as the function is importable by the daemon worker.

    The declaration is available as ``task_spec``, and is what a graph places and links against.

    Example usage:

    >>> from aiida.engine import submit, task
    >>>
    >>> @task(outputs=['total', 'product'])
    >>> def sum_product(x, y):
    >>>     return x + y, x * y
    >>>
    >>> node = submit(sum_product, x=2, y=3)

    Output ports are taken from ``outputs`` when given, otherwise from the return annotation: a ``TypedDict``
    declares one port per field, any other annotation a single ``result`` port. Without either, the output
    namespace stays dynamic, as it is for a calcfunction.

    :param function: The function to decorate.
    :param outputs: Names of the output ports to declare.
    :param identifier: Name of the task, which defaults to the name of the function.
    :return: The decorated function, carrying its ``task_spec``.
    """

    def decorator(function: t.Callable[P, R_co]) -> ProcessFunctionType[P, R_co, CalcFunctionNode]:
        decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess, outputs=outputs)(function)

        # Build the process spec eagerly, so an invalid declaration is reported where the task is defined rather
        # than when it is first launched.
        decorated.process_class.spec()  # type: ignore[attr-defined]

        decorated.task_spec = TaskSpec.from_process(decorated, identifier=identifier)  # type: ignore[attr-defined]
        return decorated  # type: ignore[return-value]

    if function is not None:
        return decorator(function)

    return decorator

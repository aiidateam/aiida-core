###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Class and decorators to generate processes out of simple python functions."""

from __future__ import annotations

import collections
import functools
import inspect
import itertools
import logging
import signal
import sys
import types
import typing as t
from typing import TYPE_CHECKING

import docstring_parser

from aiida.common.lang import override
from aiida.manage import get_manager
from aiida.orm import (
    Bool,
    CalcFunctionNode,
    Data,
    Dict,
    Float,
    Int,
    List,
    ProcessNode,
    Str,
    WorkFunctionNode,
    to_aiida_type,
)
from aiida.orm.utils.mixins import FunctionCalculationMixin

from .process import Process
from .process_spec import ProcessSpec

try:
    UnionType = types.UnionType
except AttributeError:
    # This type is not available for Python 3.9 and older
    UnionType = None  # type: ignore[assignment,misc]

try:
    from typing import ParamSpec
except ImportError:
    # Fallback for Python 3.9 and older
    from typing_extensions import ParamSpec  # type: ignore[assignment]

try:
    get_annotations = inspect.get_annotations
except AttributeError:
    # This is the backport for Python 3.9 and older
    from get_annotations import get_annotations  # type: ignore[no-redef]

if TYPE_CHECKING:
    from .exit_code import ExitCode

__all__ = ('FunctionProcess', 'calcfunction', 'workfunction')

LOGGER = logging.getLogger(__name__)

FunctionType = t.TypeVar('FunctionType', bound=t.Callable[..., t.Any])


def get_stack_size(size: int = 2) -> int:  # type: ignore[return]
    """Return the stack size for the caller's frame.

    This solution is taken from https://stackoverflow.com/questions/34115298/ as a more performant alternative to the
    naive ``len(inspect.stack())` solution. This implementation is about three orders of magnitude faster compared to
    the naive solution and it scales especially well for larger stacks, which will be usually the case for the usage
    of ``aiida-core``. However, it does use the internal ``_getframe`` of the ``sys`` standard library. It this ever
    were to stop working, simply switch to using ``len(inspect.stack())``.

    :param size: Hint for the expected stack size.
    :returns: The stack size for caller's frame.
    """
    frame = sys._getframe(size)
    try:
        for size in itertools.count(size, 8):  # noqa: PLR1704
            frame = frame.f_back.f_back.f_back.f_back.f_back.f_back.f_back.f_back  # type: ignore[assignment,union-attr]
    except AttributeError:
        while frame:  # type: ignore[truthy-bool]
            frame = frame.f_back  # type: ignore[assignment]
            size += 1
        return size - 1  # type: ignore[unreachable]


P = ParamSpec('P')
R_co = t.TypeVar('R_co', covariant=True)
N = t.TypeVar('N', bound=ProcessNode)


class ProcessFunctionType(t.Protocol, t.Generic[P, R_co, N]):
    """Protocol for a decorated process function."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...

    def run(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...

    def run_get_pk(self, *args: P.args, **kwargs: P.kwargs) -> tuple[dict[str, t.Any] | None, int]: ...

    def run_get_node(self, *args: P.args, **kwargs: P.kwargs) -> tuple[dict[str, t.Any] | None, N]: ...

    is_process_function: bool

    node_class: t.Type[N]

    process_class: t.Type[Process]

    recreate_from: t.Callable[[N], Process]

    spec: t.Callable[[], ProcessSpec]


def calcfunction(function: t.Callable[P, R_co]) -> ProcessFunctionType[P, R_co, CalcFunctionNode]:
    """A decorator to turn a standard python function into a calcfunction.
    Example usage:

    >>> from aiida.orm import Int
    >>>
    >>> # Define the calcfunction
    >>> @calcfunction
    >>> def sum(a, b):
    >>>    return a + b
    >>> # Run it with some input
    >>> r = sum(Int(4), Int(5))
    >>> print(r)
    9
    >>> r.base.links.get_incoming().all() # doctest: +SKIP
    [Neighbor(link_type='', link_label='result',
    node=<CalcFunctionNode: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>)]
    >>> r.base.links.get_incoming().get_node_by_label('result').base.links.get_incoming().all_nodes()
    [4, 5]

    :param function: The function to decorate.
    :return: The decorated function.
    """
    return process_function(node_class=CalcFunctionNode)(function)  # type: ignore[arg-type]


def workfunction(function: t.Callable[P, R_co]) -> ProcessFunctionType[P, R_co, WorkFunctionNode]:
    """A decorator to turn a standard python function into a workfunction.
    Example usage:

    >>> from aiida.orm import Int
    >>>
    >>> # Define the workfunction
    >>> @workfunction
    >>> def select(a, b):
    >>>    return a
    >>> # Run it with some input
    >>> r = select(Int(4), Int(5))
    >>> print(r)
    4
    >>> r.base.links.get_incoming().all() # doctest: +SKIP
    [Neighbor(link_type='', link_label='result',
    node=<WorkFunctionNode: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>)]
    >>> r.base.links.get_incoming().get_node_by_label('result').base.links.get_incoming().all_nodes()
    [4, 5]

    :param function: The function to decorate.
    :return: The decorated function.
    """
    return process_function(node_class=WorkFunctionNode)(function)  # type: ignore[arg-type]


def process_function(node_class: t.Type['ProcessNode']) -> t.Callable[[FunctionType], FunctionType]:
    """The base function decorator to create a FunctionProcess out of a normal python function.

    :param node_class: the ORM class to be used as the Node record for the FunctionProcess
    """

    def decorator(function: FunctionType) -> FunctionType:
        """Turn the decorated function into a FunctionProcess.

        :param callable function: the actual decorated function that the FunctionProcess represents
        :return callable: The decorated function.
        """
        process_class = FunctionProcess.build(function, node_class=node_class)

        def run_get_node(*args, **kwargs) -> tuple[dict[str, t.Any] | None, 'ProcessNode']:
            """Run the FunctionProcess with the supplied inputs in a local runner.

            :param args: input arguments to construct the FunctionProcess
            :param kwargs: input keyword arguments to construct the FunctionProcess
            :return: tuple of the outputs of the process and the process node
            """
            frame_delta = 1000
            frame_count = get_stack_size()
            stack_limit = sys.getrecursionlimit()
            LOGGER.info('Executing process function, current stack status: %d frames of %d', frame_count, stack_limit)

            # If the current frame count is more than 80% of the stack limit, or comes within 200 frames, increase the
            # stack limit by ``frame_delta``.
            if frame_count > min(0.8 * stack_limit, stack_limit - 200):
                LOGGER.warning(
                    'Current stack contains %d frames which is close to the limit of %d. Increasing the limit by %d',
                    frame_count,
                    stack_limit,
                    frame_delta,
                )
                sys.setrecursionlimit(stack_limit + frame_delta)

            manager = get_manager()
            runner = manager.get_runner()
            inputs = process_class.create_inputs(*args, **kwargs)

            # Remove all the known inputs from the kwargs
            for port in process_class.spec().inputs:
                kwargs.pop(port, None)

            # If any kwargs remain, the spec should be dynamic, so we raise if it isn't
            if kwargs and not process_class.spec().inputs.dynamic:
                raise ValueError(f'{function.__name__} does not support these kwargs: {kwargs.keys()}')

            process: Process = process_class(inputs=inputs, runner=runner)

            # Only add handlers for interrupt signal to kill the process if we are in a local and not a daemon runner.
            # Without this check, running process functions in a daemon worker would be killed if the daemon is shutdown
            current_runner = manager.get_runner()
            original_handler = None
            kill_signal = signal.SIGINT

            if not current_runner.is_daemon_runner:

                def kill_process(_num, _frame):
                    """Send the kill signal to the process in the current scope."""
                    LOGGER.critical('runner received interrupt, killing process %s', process.pid)
                    result = process.kill(msg_text='Process was killed because the runner received an interrupt')
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

            store_provenance = inputs.get('metadata', {}).get('store_provenance', True)
            if not store_provenance:
                process.node._storable = False
                process.node._unstorable_message = 'cannot store node because it was run with `store_provenance=False`'

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

        decorated_function.run = decorated_function  # type: ignore[attr-defined]
        decorated_function.run_get_pk = run_get_pk  # type: ignore[attr-defined]
        decorated_function.run_get_node = run_get_node  # type: ignore[attr-defined]
        decorated_function.is_process_function = True  # type: ignore[attr-defined]
        decorated_function.node_class = node_class  # type: ignore[attr-defined]
        decorated_function.process_class = process_class  # type: ignore[attr-defined]
        decorated_function.recreate_from = process_class.recreate_from  # type: ignore[attr-defined]
        decorated_function.spec = process_class.spec  # type: ignore[attr-defined]

        return decorated_function  # type: ignore[return-value]

    return decorator


def infer_valid_type_from_type_annotation(annotation: t.Any) -> tuple[t.Any, ...]:
    """Infer the value for the ``valid_type`` of an input port from the given function argument annotation.

    :param annotation: The annotation of a function argument as returned by ``inspect.get_annotation``.
    :returns: A tuple of valid types. If no valid types were defined or they could not be successfully parsed, an empty
        tuple is returned.
    """

    def get_type_from_annotation(annotation):
        valid_type_map = {
            bool: Bool,
            dict: Dict,
            t.Dict: Dict,
            float: Float,
            int: Int,
            list: List,
            t.List: List,
            str: Str,
        }

        if inspect.isclass(annotation) and issubclass(annotation, Data):
            return annotation

        return valid_type_map.get(annotation)

    inferred_valid_type: tuple[t.Any, ...] = ()

    if inspect.isclass(annotation):
        inferred_valid_type = (get_type_from_annotation(annotation),)
    elif t.get_origin(annotation) is t.Union or t.get_origin(annotation) is UnionType:
        inferred_valid_type = tuple(get_type_from_annotation(valid_type) for valid_type in t.get_args(annotation))
    elif t.get_origin(annotation) is t.Optional:
        inferred_valid_type = (t.get_args(annotation),)

    return tuple(valid_type for valid_type in inferred_valid_type if valid_type is not None)


class FunctionProcess(Process):
    """Function process class used for turning functions into a Process"""

    _func_args: t.Sequence[str] = ()
    _var_positional: str | None = None
    _var_keyword: str | None = None

    @staticmethod
    def _func(*_args, **_kwargs) -> dict:
        """This is used internally to store the actual function that is being
        wrapped and will be replaced by the build method.
        """
        return {}

    @staticmethod
    def build(func: FunctionType, node_class: t.Type['ProcessNode']) -> t.Type['FunctionProcess']:
        """Build a Process from the given function.

        All function arguments will be assigned as process inputs. If keyword arguments are specified then
        these will also become inputs.

        :param func: The function to build a process from
        :param node_class: Provide a custom node class to be used, has to be constructable with no arguments. It has to
            be a sub class of `ProcessNode` and the mixin :class:`~aiida.orm.utils.mixins.FunctionCalculationMixin`.

        :return: A Process class that represents the function

        """
        if (
            not issubclass(node_class, ProcessNode)  # type: ignore[redundant-expr]
            or not issubclass(node_class, FunctionCalculationMixin)
        ):
            raise TypeError('the node_class should be a sub class of `ProcessNode` and `FunctionCalculationMixin`')

        signature = inspect.signature(func)

        args: list[str] = []
        var_positional: str | None = None
        var_keyword: str | None = None

        try:
            annotations = get_annotations(func, eval_str=True)
        except Exception as exception:
            # Since we are running with ``eval_str=True`` to unstringize the annotations, the call can except if the
            # annotations are incorrect. In this case we simply want to log a warning and continue with type inference.
            LOGGER.warning(f'function `{func.__name__}` has invalid type hints: {exception}')
            annotations = {}

        if func.__doc__ is None:
            param_help_string: dict[str, str | None] = {}
            namespace_help_string = None
        else:
            try:
                parsed_docstring = docstring_parser.parse(func.__doc__)
            except Exception as exception:
                LOGGER.warning(f'function `{func.__name__}` has a docstring that could not be parsed: {exception}')
                param_help_string = {}
                namespace_help_string = None
            else:
                param_help_string = {param.arg_name: param.description for param in parsed_docstring.params}
                namespace_help_string = parsed_docstring.short_description if parsed_docstring.short_description else ''
                if parsed_docstring.long_description is not None:
                    namespace_help_string += f'\n\n{parsed_docstring.long_description}'

        for key, parameter in signature.parameters.items():
            if parameter.kind in [parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD, parameter.KEYWORD_ONLY]:
                args.append(key)

            if parameter.kind is parameter.VAR_POSITIONAL:
                var_positional = key

            if parameter.kind is parameter.VAR_KEYWORD:
                var_keyword = key

        def define(cls, spec):
            """Define the spec dynamically"""
            from plumpy.ports import UNSPECIFIED

            super().define(spec)

            for parameter in signature.parameters.values():
                if parameter.kind in [parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD]:
                    continue

                annotation = annotations.get(parameter.name)
                valid_type = infer_valid_type_from_type_annotation(annotation) or (Data,)
                help_string = param_help_string.get(parameter.name, None)

                default = parameter.default if parameter.default is not parameter.empty else UNSPECIFIED

                # If the keyword was already specified, simply override the default
                if spec.has_input(parameter.name):
                    spec.inputs[parameter.name].default = default
                    continue

                # If the default is ``None`` make sure that the port also accepts a ``NoneType``. Note that we cannot
                # use ``None`` because the validation will call ``isinstance`` which does not work when passing ``None``
                # but it does work with ``NoneType`` which is returned by calling ``type(None)``.
                if default is None:
                    valid_type += (type(None),)

                # If a default is defined and it is not a ``Data`` instance it should be serialized, but this should be
                # done lazily using a lambda, just as any port defaults should not define node instances directly as is
                # also checked by the ``spec.input`` call.
                if (
                    default is not None
                    and default != UNSPECIFIED
                    and not isinstance(default, Data)
                    and not callable(default)
                ):

                    def indirect_default(value=default):
                        return to_aiida_type(value)
                else:
                    indirect_default = default  # type: ignore[assignment]

                spec.input(
                    parameter.name,
                    valid_type=valid_type,
                    default=indirect_default,
                    serializer=to_aiida_type,
                    help=help_string,
                )

            # Set defaults for label and description based on function name and docstring, if not explicitly defined
            port_label = spec.inputs['metadata']['label']

            if not port_label.has_default():
                port_label.default = func.__name__

            spec.inputs.help = namespace_help_string

            # If the function supports varargs or kwargs then allow dynamic inputs, otherwise disallow
            spec.inputs.dynamic = var_positional is not None or var_keyword is not None

            # Function processes must have a dynamic output namespace since we do not know beforehand what outputs
            # will be returned and the valid types for the value should be `Data` nodes as well as a dictionary because
            # the output namespace can be nested.
            spec.outputs.valid_type = (Data, dict)

        return type(
            func.__qualname__,
            (FunctionProcess,),
            {
                '__module__': func.__module__,
                '__name__': func.__name__,
                '__qualname__': func.__qualname__,
                '_func': staticmethod(func),
                Process.define.__name__: classmethod(define),
                '_func_args': args,
                '_var_positional': var_positional,
                '_var_keyword': var_keyword,
                '_node_class': node_class,
            },
        )

    @classmethod
    def validate_inputs(cls, *args: t.Any, **kwargs: t.Any) -> None:
        """Validate the positional and keyword arguments passed in the function call.

        :raises TypeError: if more positional arguments are passed than the function defines
        """
        nargs = len(args)
        nparameters = len(cls._func_args)

        # If the number of positional arguments passed is larger than the number of explicitly defined parameters in the
        # signature and the function does not support variable positional arguments the inputs are invalid and we raise.
        # If we don't, some of the passed arguments, intended to be positional arguments, will be misinterpreted as
        # keyword arguments, but they won't have an explicit name to use for the link label, causing the input link to
        # be completely lost. If the function supports variadic arguments, however, additional args should be accepted.
        if nargs > nparameters and cls._var_positional is None:
            name = cls._func.__name__
            raise TypeError(f'{name}() takes {nparameters} positional arguments but {nargs} were given')

    @classmethod
    def create_inputs(cls, *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
        """Create the input dictionary for the ``FunctionProcess``."""
        cls.validate_inputs(*args, **kwargs)

        # The complete input dictionary consists of the keyword arguments...
        inputs = dict(kwargs or {})
        arguments = list(args)

        # ... and then the positional arguments need be added. Arguments with an explicit positional argument simply use
        # the argument name as the key in the dictionary explicit label. For variable positional arguments, the label is
        # constructed based on the name used for the variable positional arguments, which is stored in the
        # ``cls._var_positional`` class attribute and is suffixed with the index. If the auto-generated label would
        # overlap with an existing label (i.e. from one of the keyword arguments) an exception is raised.
        for name, parameter in inspect.signature(cls._func).parameters.items():
            if parameter.kind in [parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD]:
                try:
                    inputs[name] = arguments.pop(0)
                except IndexError:
                    pass
            elif name == cls._var_positional and parameter.kind is parameter.VAR_POSITIONAL:
                for index, arg in enumerate(arguments):
                    label = f'{cls._var_positional}_{index}'
                    if label in inputs:
                        raise RuntimeError(
                            f'variadic argument with index `{index}` would get the label `{label}` but this is already '
                            'in use by another function argument with the exact same name. To avoid this error, please '
                            f'change the name of argument `{label}` to something else.'
                        )
                    inputs[label] = arg

        return inputs

    @classmethod
    def get_or_create_db_record(cls) -> 'ProcessNode':
        return cls._node_class()

    def __init__(self, *args, **kwargs) -> None:
        if kwargs.get('enable_persistence', False):
            raise RuntimeError('Cannot persist a function process')
        super().__init__(enable_persistence=False, *args, **kwargs)  # type: ignore[misc]

    @property
    def process_class(self) -> t.Callable[..., t.Any]:
        """Return the class that represents this Process, for the FunctionProcess this is the function itself.

        For a standard Process or sub class of Process, this is the class itself. However, for legacy reasons,
        the Process class is a wrapper around another class. This function returns that original class, i.e. the
        class that really represents what was being executed.

        :return: A Process class that represents the function

        """
        return self._func

    def execute(self) -> dict[str, t.Any] | None:
        """Execute the process."""
        result = super().execute()

        # FunctionProcesses can return a single value as output, and not a dictionary, so we should also return that
        if result and len(result) == 1 and self.SINGLE_OUTPUT_LINKNAME in result:
            return result[self.SINGLE_OUTPUT_LINKNAME]

        return result

    @override
    def _setup_db_record(self) -> None:
        """Set up the database record for the process."""
        super()._setup_db_record()
        self.node.store_source_info(self._func)

    @override
    async def run(self) -> 'ExitCode' | None:
        """Run the process."""
        from .exit_code import ExitCode

        # The following conditional is required for the caching to properly work. Even if the source node has a process
        # state of `Finished` the cached process will still enter the running state. The process state will have then
        # been overridden by the engine to `Running` so we cannot check that, but if the `exit_status` is anything other
        # than `None`, it should mean this node was taken from the cache, so the process should not be rerun.
        if self.node.exit_status is not None:
            return ExitCode(self.node.exit_status, self.node.exit_message)

        # Now the original functions arguments need to be reconstructed from the inputs to the process, as they were
        # passed to the original function call. To do so, all positional parameters are popped from the inputs
        # dictionary and added to the positional arguments list.
        args = []
        kwargs: dict[str, Data] = {}
        inputs = dict(self.inputs or {})

        for name, parameter in inspect.signature(self._func).parameters.items():
            if parameter.kind in [parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD]:
                args.append(inputs.pop(name))
            elif parameter.kind is parameter.VAR_POSITIONAL:
                for key in [key for key in inputs.keys() if key.startswith(f'{name}_')]:
                    args.append(inputs.pop(key))

        # Any inputs that correspond to metadata ports were not part of the original function signature but were added
        # by the process function decorator, so these have to be removed.
        for key in [key for key, port in self.spec().inputs.items() if port.is_metadata]:
            inputs.pop(key, None)

        # The remaining inputs have to be keyword arguments.
        kwargs.update(**inputs)

        result = self._func(*args, **kwargs)

        if result is None or isinstance(result, ExitCode):  # type: ignore[redundant-expr]
            return result  # type: ignore[unreachable]

        if isinstance(result, Data):  # type: ignore[unreachable]
            self.out(self.SINGLE_OUTPUT_LINKNAME, result)  # type: ignore[unreachable]
        elif isinstance(result, collections.abc.Mapping):
            for name, value in result.items():
                self.out(name, value)
        else:
            raise TypeError(
                "Function process returned an output with unsupported type '{}'\n"
                'Must be a Data type or a mapping of {{string: Data}}'.format(result.__class__)
            )

        return ExitCode()

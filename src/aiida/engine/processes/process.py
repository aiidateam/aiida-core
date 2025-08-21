###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The AiiDA process class"""

from __future__ import annotations

import asyncio
import collections
import copy
import enum
import inspect
import logging
import traceback
from collections.abc import Mapping
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)
from uuid import UUID

import plumpy.exceptions
import plumpy.futures
import plumpy.persistence
import plumpy.processes
from kiwipy.communications import UnroutableError
from plumpy.process_states import Finished, ProcessState
from plumpy.processes import ConnectionClosed  # type: ignore[attr-defined]
from plumpy.processes import Process as PlumpyProcess
from plumpy.utils import AttributesFrozendict

from aiida import orm
from aiida.common import exceptions
from aiida.common.extendeddicts import AttributeDict
from aiida.common.lang import classproperty, override
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.engine.utils import InterruptableFuture
from aiida.orm.implementation.utils import clean_value
from aiida.orm.nodes.process.calculation.calcjob import CalcJobNode
from aiida.orm.utils import serialize

from .builder import ProcessBuilder
from .exit_code import ExitCode, ExitCodesNamespace
from .ports import PORT_NAMESPACE_SEPARATOR, InputPort, OutputPort, PortNamespace
from .process_spec import ProcessSpec
from .utils import prune_mapping

if TYPE_CHECKING:
    from aiida.engine.runners import Runner

__all__ = ('Process', 'ProcessState')


@plumpy.persistence.auto_persist('_parent_pid', '_enable_persistence')
class Process(PlumpyProcess):
    """This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """

    _cancelling_scheduler_job: asyncio.Task | None = None
    _node_class = orm.ProcessNode
    _spec_class = ProcessSpec

    SINGLE_OUTPUT_LINKNAME: str = 'result'

    class SaveKeys(enum.Enum):
        """Keys used to identify things in the saved instance state bundle."""

        CALC_ID = 'calc_id'

    @classmethod
    def spec(cls) -> ProcessSpec:
        return super().spec()  # type: ignore[return-value]

    @classmethod
    def define(cls, spec: ProcessSpec) -> None:  # type: ignore[override]
        """Define the specification of the process, including its inputs, outputs and known exit codes.

        A `metadata` input namespace is defined, with optional ports that are not stored in the database.

        """
        super().define(spec)
        spec.input_namespace(spec.metadata_key, required=False, is_metadata=True)
        spec.input(
            f'{spec.metadata_key}.store_provenance',
            valid_type=bool,
            default=True,
            help='If set to `False` provenance will not be stored in the database.',
        )
        spec.input(
            f'{spec.metadata_key}.description',
            valid_type=str,
            required=False,
            help='Description to set on the process node.',
        )
        spec.input(
            f'{spec.metadata_key}.label', valid_type=str, required=False, help='Label to set on the process node.'
        )
        spec.input(
            f'{spec.metadata_key}.call_link_label',
            valid_type=str,
            default='CALL',
            help='The label to use for the `CALL` link if the process is called by another process.',
        )
        spec.input(
            'metadata.disable_cache',
            required=False,
            valid_type=bool,
            help='Do not consider the cache for this process, ignoring all other caching configuration rules.',
        )
        spec.inputs.valid_type = orm.Data
        spec.inputs.dynamic = False  # Settings a ``valid_type`` automatically makes it dynamic, so we reset it again
        spec.exit_code(
            1, 'ERROR_UNSPECIFIED', invalidates_cache=True, message='The process has failed with an unspecified error.'
        )
        spec.exit_code(
            2, 'ERROR_LEGACY_FAILURE', invalidates_cache=True, message='The process failed with legacy failure mode.'
        )
        spec.exit_code(
            10, 'ERROR_INVALID_OUTPUT', invalidates_cache=True, message='The process returned an invalid output.'
        )
        spec.exit_code(
            11,
            'ERROR_MISSING_OUTPUT',
            invalidates_cache=True,
            message='The process did not register a required output.',
        )

    @classmethod
    def get_builder(cls) -> ProcessBuilder:
        return ProcessBuilder(cls)

    @classmethod
    def get_or_create_db_record(cls) -> orm.ProcessNode:
        """Create a process node that represents what happened in this process.

        :return: A process node
        """
        return cls._node_class()

    def __init__(
        self,
        inputs: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
        runner: Optional['Runner'] = None,
        parent_pid: Optional[int] = None,
        enable_persistence: bool = True,
    ) -> None:
        """Process constructor.

        :param inputs: process inputs
        :param logger: aiida logger
        :param runner: process runner
        :param parent_pid: id of parent process
        :param enable_persistence: whether to persist this process

        """
        from aiida.manage import manager

        self._runner = runner if runner is not None else manager.get_manager().get_runner()
        # assert self._runner.communicator is not None, 'communicator not set for runner'

        super().__init__(
            inputs=self.spec().inputs.serialize(inputs),
            logger=logger,
            loop=self._runner.loop,
            communicator=self._runner.communicator,
        )

        self._node: Optional[orm.ProcessNode] = None
        self._parent_pid = parent_pid
        self._enable_persistence = enable_persistence
        if self._enable_persistence and self.runner.persister is None:
            self.logger.warning('Disabling persistence, runner does not have a persister')
            self._enable_persistence = False

    def init(self) -> None:
        super().init()
        if self._logger is None:
            self.set_logger(self.node.logger)

    @classmethod
    def get_exit_statuses(cls, exit_code_labels: Iterable[str]) -> List[int]:
        """Return the exit status (integers) for the given exit code labels.

        :param exit_code_labels: a list of strings that reference exit code labels of this process class
        :return: list of exit status integers that correspond to the given exit code labels
        :raises AttributeError: if at least one of the labels does not correspond to an existing exit code
        """
        exit_codes = cls.exit_codes
        return [getattr(exit_codes, label).status for label in exit_code_labels]

    @classproperty
    def exit_codes(cls) -> ExitCodesNamespace:  # noqa: N805
        """Return the namespace of exit codes defined for this WorkChain through its ProcessSpec.

        The namespace supports getitem and getattr operations with an ExitCode label to retrieve a specific code.
        Additionally, the namespace can also be called with either the exit code integer status to retrieve it.

        :returns: ExitCodesNamespace of ExitCode named tuples

        """
        return cls.spec().exit_codes

    @classproperty
    def spec_metadata(cls) -> PortNamespace:  # noqa: N805
        """Return the metadata port namespace of the process specification of this process."""
        return cls.spec().inputs['metadata']  # type: ignore[return-value]

    @property
    def node(self) -> orm.ProcessNode:
        """Return the ProcessNode used by this process to represent itself in the database.

        :return: instance of sub class of ProcessNode
        """
        assert self._node is not None
        return self._node

    @property
    def uuid(self) -> str:  # type: ignore[override]
        """Return the UUID of the process which corresponds to the UUID of its associated `ProcessNode`.

        :return: the UUID associated to this process instance
        """
        return self.node.uuid

    @property
    def inputs(self) -> AttributesFrozendict:
        """Return the inputs attribute dictionary or an empty one.

        This overrides the property of the base class because that can also return ``None``. This override ensures
        calling functions that they will always get an instance of ``AttributesFrozenDict``.
        """
        return super().inputs or AttributesFrozendict()

    @property
    def metadata(self) -> AttributeDict:
        """Return the metadata that were specified when this process instance was launched.

        :return: metadata dictionary

        """
        try:
            return self.inputs.metadata
        except (AssertionError, AttributeError):
            return AttributeDict()

    def _save_checkpoint(self) -> None:
        """Save the current state in a chechpoint if persistence is enabled and the process state is not terminal

        If the persistence call excepts with a PersistenceError, it will be caught and a warning will be logged.
        """
        if self._enable_persistence and not self._state.is_terminal():
            if self.runner.persister is None:
                self.logger.exception(
                    'No persister set to save checkpoint, this means you will '
                    'not be able to restart in case of a crash until the next successful checkpoint.'
                )
                return None
            try:
                self.runner.persister.save_checkpoint(self)
            except plumpy.exceptions.PersistenceError:
                self.logger.exception(
                    'Exception trying to save checkpoint, this means you will '
                    'not be able to restart in case of a crash until the next successful checkpoint.'
                )

    @override
    def save_instance_state(
        self, out_state: MutableMapping[str, Any], save_context: Optional[plumpy.persistence.LoadSaveContext]
    ) -> None:
        """Save instance state.

        See documentation of :meth:`!plumpy.processes.Process.save_instance_state`.
        """
        super().save_instance_state(out_state, save_context)

        if self.metadata.store_provenance:
            assert self.node.is_stored

        out_state[self.SaveKeys.CALC_ID.value] = self.pid

    def get_provenance_inputs_iterator(self) -> Iterator[Tuple[str, Union[InputPort, PortNamespace]]]:
        """Get provenance input iterator.

        :rtype: filter
        """
        return filter(lambda kv: not kv[0].startswith('_'), self.inputs.items())

    @override
    def load_instance_state(
        self, saved_state: MutableMapping[str, Any], load_context: plumpy.persistence.LoadSaveContext
    ) -> None:
        """Load instance state.

        :param saved_state: saved instance state
        :param load_context:

        """
        from aiida.manage import manager

        if 'runner' in load_context:
            self._runner = load_context.runner
        else:
            self._runner = manager.get_manager().get_runner()

        load_context = load_context.copyextend(loop=self._runner.loop, communicator=self._runner.communicator)
        super().load_instance_state(saved_state, load_context)

        if self.SaveKeys.CALC_ID.value in saved_state:
            self._node = orm.load_node(saved_state[self.SaveKeys.CALC_ID.value])  # type: ignore[assignment]
            self._pid = self.node.pk
        else:
            self._pid = self._create_and_setup_db_record()

        self.node.logger.info(f'Loaded process<{self.node.pk}> from saved state')

    def kill(self, msg_text: str | None = None, force_kill: bool = False) -> Union[bool, plumpy.futures.Future]:
        """Kill the process and all the children calculations it called

        :param msg: message
        """
        self.node.logger.info(f'Request to kill Process<{self.node.pk}>')

        if self.killed():
            # Already killed
            return True

        if self.has_terminated():
            # Can't kill
            return False

        # Cancel scheduler job
        if not force_kill and isinstance(self.node, CalcJobNode):
            if self._killing:
                self._killing.cancel()

            if self._cancelling_scheduler_job:
                self._cancelling_scheduler_job.cancel()
                self.node.logger.report('Found active scheduler job cancelation that will be rescheduled.')

            from .calcjobs.tasks import task_kill_job

            coro = self._launch_task(task_kill_job, self.node, self.runner.transport)
            self._cancelling_scheduler_job = asyncio.create_task(coro)
            try:
                self.loop.run_until_complete(self._cancelling_scheduler_job)
            except Exception as exc:
                self.node.logger.error(f'While cancelling the scheduler job an error was raised: {exc}')
                return False

        result = super().kill(msg_text, force_kill)

        had_been_terminated = self.has_terminated()

        # Only kill children if we could be killed ourselves
        if result is not False and not had_been_terminated:
            killing = []
            for child in self.node.called:
                if self.runner.controller is None:
                    self.logger.info('no controller available to kill child<%s>', child.pk)
                    continue
                try:
                    result = self.runner.controller.kill_process(child.pk, msg_text=f'Killed by parent<{self.node.pk}>')
                    result = asyncio.wrap_future(result)
                    if asyncio.isfuture(result):
                        killing.append(result)
                except ConnectionClosed:
                    self.logger.info('no connection available to kill child<%s>', child.pk)
                except UnroutableError:
                    self.logger.info('kill signal was unable to reach child<%s>', child.pk)

            if asyncio.isfuture(result):
                # We ourselves are waiting to be killed so add it to the list
                killing.append(result)

            if killing:
                # We are waiting for things to be killed, so return the 'gathered' future
                kill_future = plumpy.futures.gather(*killing)
                result = self.loop.create_future()

                def done(done_future: plumpy.futures.Future):
                    is_all_killed = all(done_future.result())
                    result.set_result(is_all_killed)

                kill_future.add_done_callback(done)

        return result

    async def _launch_task(self, coro, *args, **kwargs):
        """Launch a coroutine as a task, making sure to make it interruptable."""
        import functools

        from aiida.engine.utils import interruptable_task

        self._task: Union[InterruptableFuture, None]

        task_fn = functools.partial(coro, *args, **kwargs)
        try:
            self._task = interruptable_task(task_fn)
            result = await self._task
            return result
        finally:
            self._task = None

    @override
    def out(self, output_port: str, value: Any = None) -> None:
        """Attach output to output port.

        The name of the port will be used as the link label.

        :param output_port: name of output port
        :param value: value to put inside output port

        """
        if value is None:
            # In this case assume that output_port is the actual value and there is just one return value
            value = output_port
            output_port = self.SINGLE_OUTPUT_LINKNAME

        return super().out(output_port, value)

    def out_many(self, out_dict: Dict[str, Any]) -> None:
        """Attach outputs to multiple output ports.

        Keys of the dictionary will be used as output port names, values as outputs.

        :param out_dict: output dictionary
        :type out_dict: dict
        """
        for key, value in out_dict.items():
            self.out(key, value)

    def on_create(self) -> None:
        """Called when a Process is created."""
        super().on_create()
        # If parent PID hasn't been supplied try to get it from the stack
        if self._parent_pid is None and Process.current():
            current = Process.current()
            if isinstance(current, Process):
                self._parent_pid = current.pid  # type: ignore[assignment]
        self._pid = self._create_and_setup_db_record()

    @override
    def on_entered(self, from_state: Optional[plumpy.process_states.State]) -> None:
        """After entering a new state, save a checkpoint and update the latest process state change timestamp."""
        from plumpy import ProcessState

        from aiida.engine.utils import set_process_state_change_timestamp

        if self._state.LABEL is ProcessState.EXCEPTED:
            # The process is already excepted so simply update the process state on the node and let the process
            # complete the state transition to the terminal state. If another exception is raised during this exception
            # handling, the process transitioning is cut short and never makes it to the terminal state.
            self.node.set_process_state(self._state.LABEL)
            return

        # We need to guarantee that the process state gets updated even if the ``update_outputs`` call excepts, for
        # example if the process implementation attaches an invalid output through ``Process.out``, and so we call the
        # ``ProcessNode.set_process_state`` in the finally-clause. This way the state gets properly set on the node even
        # if the process is transitioning to the terminal excepted state.
        try:
            self.update_outputs()
        except ValueError:
            raise
        finally:
            self.node.set_process_state(self._state.LABEL)  # type: ignore[arg-type]

        self._save_checkpoint()
        set_process_state_change_timestamp(self.node)

        # The updating of outputs and state has to be performed before the super is called because the super will
        # broadcast state changes and parent processes may start running again before the state change is completed. It
        # is possible that they will read the old process state and outputs that they check may not yet have been
        # attached.
        super().on_entered(from_state)

    @override
    def on_terminated(self) -> None:
        """Called when a Process enters a terminal state."""
        super().on_terminated()
        if self._enable_persistence:
            try:
                assert self.runner.persister is not None
                self.runner.persister.delete_checkpoint(self.pid)
            except Exception as error:
                self.logger.exception('Failed to delete checkpoint: %s', error)

        try:
            self.node.seal()
        except exceptions.ModificationNotAllowed:
            pass

    @override
    def on_except(self, exc_info: Tuple[Any, Exception, TracebackType]) -> None:
        """Log the exception by calling the report method with formatted stack trace from exception info object
        and store the exception string as a node attribute

        :param exc_info: the sys.exc_info() object (type, value, traceback)
        """
        super().on_except(exc_info)
        self.node.set_exception(''.join(traceback.format_exception(exc_info[0], exc_info[1], None)).rstrip())
        self.report(''.join(traceback.format_exception(*exc_info)))

    @override
    def on_finish(self, result: Union[int, ExitCode, None], successful: bool) -> None:
        """Set the finish status on the process node.

        :param result: result of the process
        :param successful: whether execution was successful

        """
        super().on_finish(result, successful)

        if result is None:
            if not successful:
                result = self.exit_codes.ERROR_MISSING_OUTPUT
            else:
                result = ExitCode()

        if isinstance(result, int):
            self.node.set_exit_status(result)
        elif isinstance(result, ExitCode):
            self.node.set_exit_status(result.status)
            self.node.set_exit_message(result.message)
        else:
            raise ValueError(
                f'the result should be an integer, ExitCode or None, got {type(result)} {result} {self.pid}'
            )

    @override
    def on_paused(self, msg: Optional[str] = None) -> None:
        """The Process was paused so set the paused attribute on the process node

        :param msg: message

        """
        super().on_paused(msg)
        self._save_checkpoint()
        self.node.pause()

    @override
    def on_playing(self) -> None:
        """The Process was unpaused so remove the paused attribute on the process node"""
        super().on_playing()
        self.node.unpause()

    @override
    def on_output_emitting(self, output_port: str, value: Any) -> None:
        """The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted

        """
        super().on_output_emitting(output_port, value)

        # Note that `PortNamespaces` should be able to receive non `Data` types such as a normal dictionary
        if isinstance(output_port, OutputPort) and not isinstance(value, orm.Data):
            raise TypeError(f'Processes can only return `orm.Data` instances as output, got {value.__class__}')

    def set_status(self, status: Optional[str]) -> None:
        """The status of the Process is about to be changed, so we reflect this is in node's attribute proxy.

        :param status: the status message

        """
        super().set_status(status)
        self.node.set_process_status(status)

    def submit(self, process: Type['Process'], inputs: dict[str, Any] | None = None, **kwargs) -> orm.ProcessNode:
        """Submit process for execution.

        :param process: The process class.
        :param inputs: The dictionary of process inputs.
        :return: The process node.
        """
        return self.runner.submit(process, inputs, **kwargs)

    @property
    def runner(self) -> 'Runner':
        """Get process runner."""
        return self._runner

    def get_parent_calc(self) -> Optional[orm.ProcessNode]:
        """Get the parent process node

        :return: the parent process node if there is one

        """
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        return orm.load_node(pk=self._parent_pid)  # type: ignore[return-value]

    @classmethod
    def build_process_type(cls) -> str:
        """The process type.

        :return: string of the process type

        Note: This could be made into a property 'process_type' but in order to have it be a property of the class
        it would need to be defined in the metaclass, see https://bugs.python.org/issue20659
        """
        from aiida.plugins.entry_point import get_entry_point_string_from_class

        class_module = cls.__module__
        class_name = cls.__name__

        # If the process is a registered plugin the corresponding entry point will be used as process type
        process_type = get_entry_point_string_from_class(class_module, class_name)

        # If no entry point was found, default to fully qualified path name
        if process_type is None:
            return f'{class_module}.{class_name}'

        return process_type

    def report(self, msg: str, *args, **kwargs) -> None:
        """Log a message to the logger, which should get saved to the database through the attached DbLogHandler.

        The pk, class name and function name of the caller are prepended to the given message

        :param msg: message to log
        :param args: args to pass to the log call
        :param kwargs: kwargs to pass to the log call

        """
        message = f'[{self.node.pk}|{self.__class__.__name__}|{inspect.stack()[1][3]}]: {msg}'
        self.logger.log(LOG_LEVEL_REPORT, message, *args, **kwargs)

    def _create_and_setup_db_record(self) -> Union[int, UUID]:
        """Create and setup the database record for this process

        :return: the uuid or pk of the process

        """
        self._node = self.get_or_create_db_record()
        self._setup_db_record()
        if self.metadata.store_provenance:
            try:
                self.node.store_all()
                if self.node.is_finished_ok:
                    self._state = Finished(self, None, True)
                    for entry in self.node.base.links.get_outgoing(link_type=LinkType.RETURN):
                        if entry.link_label.endswith(f'_{entry.node.pk}'):
                            continue
                        label = entry.link_label.replace(PORT_NAMESPACE_SEPARATOR, self.spec().namespace_separator)
                        self.out(label, entry.node)
                    # This is needed for CalcJob. In that case, the outputs are
                    # returned regardless of whether they end in '_pk'
                    for entry in self.node.base.links.get_outgoing(link_type=LinkType.CREATE):
                        label = entry.link_label.replace(PORT_NAMESPACE_SEPARATOR, self.spec().namespace_separator)
                        self.out(label, entry.node)
            except exceptions.ModificationNotAllowed:
                # The calculation was already stored
                pass
        else:
            # Cannot persist the process if were not storing provenance because that would require a stored node
            self._enable_persistence = False

        if self.node.pk is not None:
            return self.node.pk

        return UUID(self.node.uuid)

    @override
    def encode_input_args(self, inputs: Dict[str, Any]) -> str:
        """Encode input arguments such that they may be saved in a Bundle

        :param inputs: A mapping of the inputs as passed to the process
        :return: The encoded (serialized) inputs
        """
        return serialize.serialize(inputs)

    @override
    def decode_input_args(self, encoded: str) -> Dict[str, Any]:
        """Decode saved input arguments as they came from the saved instance state Bundle

        :param encoded: encoded (serialized) inputs
        :return: The decoded input args
        """
        return serialize.deserialize_unsafe(encoded)

    def update_outputs(self) -> None:
        """Attach new outputs to the node since the last call.

        Does nothing, if self.metadata.store_provenance is False.
        """
        if self.metadata.store_provenance is False:
            return

        outputs_flat = self._flat_outputs()
        outputs_stored = self.node.base.links.get_outgoing(
            link_type=(LinkType.CREATE, LinkType.RETURN)
        ).all_link_labels()
        outputs_new = set(outputs_flat.keys()) - set(outputs_stored)

        for link_label, output in outputs_flat.items():
            if link_label not in outputs_new:
                continue

            if isinstance(self.node, orm.CalculationNode):
                output.base.links.add_incoming(self.node, LinkType.CREATE, link_label)
            elif isinstance(self.node, orm.WorkflowNode):
                output.base.links.add_incoming(self.node, LinkType.RETURN, link_label)

            output.store()

    def _build_process_label(self) -> str:
        """Construct the process label that should be set on ``ProcessNode`` instances for this process class.

        .. note:: By default this returns the name of the process class itself. It can be overridden by ``Process``
            subclasses to provide a more specific label.

        :returns: The process label to use for ``ProcessNode`` instances.
        """
        return self.__class__.__name__

    def _setup_db_record(self) -> None:
        """Create the database record for this process and the links with respect to its inputs

        This function will set various attributes on the node that serve as a proxy for attributes of the Process.
        This is essential as otherwise this information could only be introspected through the Process itself, which
        is only available to the interpreter that has it in memory. To make this data introspectable from any
        interpreter, for example for the command line interface, certain Process attributes are proxied through the
        calculation node.

        In addition, the parent calculation will be setup with a CALL link if applicable and all inputs will be
        linked up as well.
        """
        assert not self.node.is_sealed, 'process node cannot be sealed when setting up the database record'

        # Store important process attributes in the node proxy
        self.node.set_process_state(None)
        self.node.set_process_label(self._build_process_label())
        self.node.set_process_type(self.__class__.build_process_type())

        parent_calc = self.get_parent_calc()

        if parent_calc and self.metadata.store_provenance:
            if isinstance(parent_calc, orm.CalculationNode):
                raise exceptions.InvalidOperation('calling processes from a calculation type process is forbidden.')

            if isinstance(self.node, orm.CalculationNode):
                self.node.base.links.add_incoming(parent_calc, LinkType.CALL_CALC, self.metadata.call_link_label)

            elif isinstance(self.node, orm.WorkflowNode):
                self.node.base.links.add_incoming(parent_calc, LinkType.CALL_WORK, self.metadata.call_link_label)

        self._setup_metadata(copy.copy(dict(self.inputs.metadata)))
        self._setup_version_info()
        self._setup_inputs()

    def _setup_version_info(self) -> dict[str, Any]:
        """Store relevant plugin version information."""
        version_info = self.runner.plugin_version_provider.get_version_info(self.__class__)
        self.node.base.attributes.set_many(version_info)
        return version_info

    def _setup_metadata(self, metadata: dict) -> None:
        """Store the metadata on the ProcessNode."""
        for name, value in metadata.items():
            if name in ['store_provenance', 'dry_run', 'call_link_label', 'disable_cache']:
                continue

            if name == 'label':
                self.node.label = value
            elif name == 'description':
                self.node.description = value
            else:
                raise RuntimeError(f'unsupported metadata key: {name}')

        # Store JSON-serializable values of ``metadata`` ports in the node's attributes. Note that instead of passing in
        # the ``metadata`` inputs directly, the entire namespace of raw inputs is passed. The reason is that although
        # currently in ``aiida-core`` all input ports with ``is_metadata=True`` in the port specification are located
        # within the ``metadata`` port namespace, this may not always be the case. The ``_filter_serializable_metadata``
        # method will filter out all ports that set ``is_metadata=True`` no matter where in the namespace they are
        # defined so this approach is more robust for the future.
        serializable_inputs = self._filter_serializable_metadata(self.spec().inputs, self.raw_inputs)
        pruned = prune_mapping(serializable_inputs)
        self.node.set_metadata_inputs(pruned)

    def _setup_inputs(self) -> None:
        """Create the links between the input nodes and the ProcessNode that represents this process."""
        for name, node in self._flat_inputs().items():
            # Certain processes allow to specify ports with `None` as acceptable values
            if node is None:
                continue

            # Need this special case for tests that use ProcessNodes as classes
            if isinstance(self.node, orm.CalculationNode):
                self.node.base.links.add_incoming(node, LinkType.INPUT_CALC, name)

            elif isinstance(self.node, orm.WorkflowNode):
                self.node.base.links.add_incoming(node, LinkType.INPUT_WORK, name)

    def _filter_serializable_metadata(
        self,
        port: Union[None, InputPort, PortNamespace],
        port_value: Any,
    ) -> Union[Any, None]:
        """Return the inputs that correspond to ports with ``is_metadata=True`` and that are JSON serializable.

        The function is called recursively for any port namespaces.

        :param port: An ``InputPort`` or ``PortNamespace``. If an ``InputPort`` that specifies ``is_metadata=True`` the
            ``port_value`` is returned. For a ``PortNamespace`` this method is called recursively for the keys within
            the namespace and the resulting dictionary is returned, omitting ``None`` values. If either ``port`` or
            ``port_value`` is ``None``, ``None`` is returned.
        :return: The ``port_value`` where all inputs that do no correspond to a metadata port or are not JSON
            serializable, have been filtered out.
        """
        if port is None or port_value is None:
            return None

        if isinstance(port, InputPort):
            if not port.is_metadata:
                return None

            try:
                clean_value(port_value)
            except exceptions.ValidationError:
                return None
            return port_value

        result = {}

        for key, value in port_value.items():
            if key not in port:
                continue

            metadata_value = self._filter_serializable_metadata(port[key], value)  # type: ignore[arg-type]

            if metadata_value is None:
                continue

            result[key] = metadata_value

        return result or None

    def _flat_inputs(self) -> Dict[str, Any]:
        """Return a flattened version of the parsed inputs dictionary.

        The eventual keys will be a concatenation of the nested keys. Note that the `metadata` dictionary, if present,
        is not passed, as those are dealt with separately in `_setup_metadata`.

        :return: flat dictionary of parsed inputs

        """
        inputs = {key: value for key, value in self.inputs.items() if key != self.spec().metadata_key}
        return dict(self._flatten_inputs(self.spec().inputs, inputs))

    def _flat_outputs(self) -> Dict[str, Any]:
        """Return a flattened version of the registered outputs dictionary.

        The eventual keys will be a concatenation of the nested keys.

        :return: flat dictionary of parsed outputs
        """
        return dict(self._flatten_outputs(self.spec().outputs, self.outputs))

    def _flatten_inputs(
        self,
        port: Union[None, InputPort, PortNamespace],
        port_value: Any,
        parent_name: str = '',
        separator: str = PORT_NAMESPACE_SEPARATOR,
    ) -> List[Tuple[str, Any]]:
        """Function that will recursively flatten the inputs dictionary, omitting inputs for ports that
        are marked as being non database storable

        :param port: port against which to map the port value, can be InputPort or PortNamespace
        :param port_value: value for the current port, can be a Mapping
        :param parent_name: the parent key with which to prefix the keys
        :param separator: character to use for the concatenation of keys
        :return: flat list of inputs

        """
        if (port is None and isinstance(port_value, orm.Node)) or (
            isinstance(port, InputPort) and not (port.is_metadata or port.non_db)
        ):
            return [(parent_name, port_value)]

        if (port is None and isinstance(port_value, Mapping)) or isinstance(port, PortNamespace):
            items = []
            for name, value in port_value.items():
                prefixed_key = parent_name + separator + name if parent_name else name

                try:
                    nested_port = cast(Union[InputPort, PortNamespace], port[name]) if port else None
                except (KeyError, TypeError):
                    nested_port = None

                sub_items = self._flatten_inputs(
                    port=nested_port, port_value=value, parent_name=prefixed_key, separator=separator
                )
                items.extend(sub_items)
            return items

        assert (port is None) or (
            isinstance(port, InputPort) and (port.is_metadata or port.non_db)  # type: ignore[redundant-expr]
        )
        return []

    def _flatten_outputs(
        self,
        port: Union[None, OutputPort, PortNamespace],
        port_value: Any,
        parent_name: str = '',
        separator: str = PORT_NAMESPACE_SEPARATOR,
    ) -> List[Tuple[str, Any]]:
        """Function that will recursively flatten the outputs dictionary.

        :param port: port against which to map the port value, can be OutputPort or PortNamespace
        :param port_value: value for the current port, can be a Mapping
        :param parent_name: the parent key with which to prefix the keys
        :param separator: character to use for the concatenation of keys

        :return: flat list of outputs

        """
        if (port is None and isinstance(port_value, orm.Node)) or isinstance(port, OutputPort):
            return [(parent_name, port_value)]

        if (port is None and isinstance(port_value, Mapping)) or isinstance(port, PortNamespace):
            items = []
            for name, value in port_value.items():
                prefixed_key = parent_name + separator + name if parent_name else name

                try:
                    nested_port = cast(Union[OutputPort, PortNamespace], port[name]) if port else None
                except (KeyError, TypeError):
                    nested_port = None

                sub_items = self._flatten_outputs(
                    port=nested_port, port_value=value, parent_name=prefixed_key, separator=separator
                )
                items.extend(sub_items)
            return items

        assert port is None, port
        return []

    def exposed_inputs(
        self, process_class: Type['Process'], namespace: Optional[str] = None, agglomerate: bool = True
    ) -> AttributeDict:
        """Gather a dictionary of the inputs that were exposed for a given Process class under an optional namespace.

        :param process_class: Process class whose inputs to try and retrieve
        :param namespace: PortNamespace in which to look for the inputs
        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also be
            searched for inputs. Inputs in lower-lying namespaces take precedence.

        :returns: exposed inputs

        """
        exposed_inputs = {}

        namespace_list = self._get_namespace_list(namespace=namespace, agglomerate=agglomerate)
        for sub_namespace in namespace_list:
            # The sub_namespace None indicates the base level sub_namespace
            if sub_namespace is None:
                inputs = self.inputs
                port_namespace = self.spec().inputs
            else:
                inputs = self.inputs
                for part in sub_namespace.split('.'):
                    inputs = inputs[part]
                try:
                    port_namespace = self.spec().inputs.get_port(sub_namespace)  # type: ignore[assignment]
                except KeyError:
                    raise ValueError(f'this process does not contain the "{sub_namespace}" input namespace')

            # Get the list of ports that were exposed for the given Process class in the current sub_namespace
            exposed_inputs_list = self.spec()._exposed_inputs[sub_namespace][process_class]

            for name in port_namespace.ports.keys():
                if inputs and name in inputs and name in exposed_inputs_list:
                    exposed_inputs[name] = inputs[name]

        return AttributeDict(exposed_inputs)

    def exposed_outputs(
        self,
        node: orm.ProcessNode,
        process_class: Type['Process'],
        namespace: Optional[str] = None,
        agglomerate: bool = True,
    ) -> AttributeDict:
        """Return the outputs which were exposed from the ``process_class`` and emitted by the specific ``node``

        :param node: process node whose outputs to try and retrieve
        :param namespace: Namespace in which to search for exposed outputs.
        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also
            be searched for outputs. Outputs in lower-lying namespaces take precedence.

        :returns: exposed outputs

        """
        namespace_separator = self.spec().namespace_separator

        output_key_map = {}
        # maps the exposed name to all outputs that belong to it
        top_namespace_map = collections.defaultdict(list)
        link_types = (LinkType.CREATE, LinkType.RETURN)
        process_outputs_dict = node.base.links.get_outgoing(link_type=link_types).nested()

        for port_name in process_outputs_dict:
            top_namespace = port_name.split(namespace_separator)[0]
            top_namespace_map[top_namespace].append(port_name)

        for port_namespace in self._get_namespace_list(namespace=namespace, agglomerate=agglomerate):
            # only the top-level key is stored in _exposed_outputs
            for top_name in top_namespace_map:
                if namespace is not None and namespace not in self.spec()._exposed_outputs:
                    raise KeyError(f'the namespace `{namespace}` is not an exposed namespace.')
                if top_name in self.spec()._exposed_outputs[port_namespace][process_class]:
                    output_key_map[top_name] = port_namespace

        result = {}

        for top_name, port_namespace in output_key_map.items():
            # collect all outputs belonging to the given top_name
            for port_name in top_namespace_map[top_name]:
                if port_namespace is None:
                    result[port_name] = process_outputs_dict[port_name]
                else:
                    result[port_namespace + namespace_separator + port_name] = process_outputs_dict[port_name]

        return AttributeDict(result)

    @staticmethod
    def _get_namespace_list(namespace: Optional[str] = None, agglomerate: bool = True) -> List[Optional[str]]:
        """Get the list of namespaces in a given namespace.

        :param namespace: name space
        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also
            be searched.

        :returns: namespace list

        """
        if not agglomerate:
            return [namespace]

        namespace_list: List[Optional[str]] = [None]
        if namespace is not None:
            split_ns = namespace.split('.')
            namespace_list.extend(['.'.join(split_ns[:i]) for i in range(1, len(split_ns) + 1)])
        return namespace_list

    @classmethod
    def is_valid_cache(cls, node: orm.ProcessNode) -> bool:
        """Check if the given node can be cached from.

        Overriding this method allows ``Process`` sub-classes to modify when
        corresponding process nodes are considered as a cache.

        .. warning :: When overriding this method, make sure to return ``False``
            *at least* in all cases when ``super()._node.base.caching.is_valid_cache(node)``
            returns ``False``. Otherwise, the ``invalidates_cache`` keyword on exit
            codes may have no effect.

        """
        exit_status = node.exit_status
        if exit_status is None:
            return True
        try:
            return not cls.spec().exit_codes(exit_status).invalidates_cache
        except ValueError:
            return True


def get_query_string_from_process_type_string(process_type_string: str) -> str:
    """Take the process type string of a Node and create the queryable type string.

    :param process_type_string: the process type string
    :type process_type_string: str

    :return: string that can be used to query for subclasses of the process type using 'LIKE <string>'
    :rtype: str
    """
    if ':' in process_type_string:
        return f'{process_type_string}.'

    path = process_type_string.rsplit('.', 2)[0]
    return f'{path}.'

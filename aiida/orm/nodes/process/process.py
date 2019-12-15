# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for processes."""

import enum

from plumpy import ProcessState

from aiida.common.links import LinkType
from aiida.common.lang import classproperty
from aiida.orm.utils.mixins import Sealable

from ..node import Node

__all__ = ('ProcessNode',)


class ProcessNode(Sealable, Node):
    """
    Base class for all nodes representing the execution of a process

    This class and its subclasses serve as proxies in the database, for actual `Process` instances being run. The
    `Process` instance in memory will leverage an instance of this class (the exact sub class depends on the sub class
    of `Process`) to persist important information of its state to the database. This serves as a way for the user to
    inspect the state of the `Process` during its execution as well as a permanent record of its execution in the
    provenance graph, after the execution has terminated.
    """
    # pylint: disable=too-many-public-methods,abstract-method

    CHECKPOINT_KEY = 'checkpoints'
    EXCEPTION_KEY = 'exception'
    EXIT_MESSAGE_KEY = 'exit_message'
    EXIT_STATUS_KEY = 'exit_status'
    PROCESS_PAUSED_KEY = 'paused'
    PROCESS_LABEL_KEY = 'process_label'
    PROCESS_STATE_KEY = 'process_state'
    PROCESS_STATUS_KEY = 'process_status'

    # The link_type might not be correct while the object is being created.
    _hash_ignored_inputs = ['CALL_CALC', 'CALL_WORK']

    # Specific sub classes should be marked as cacheable when appropriate
    _cachable = False

    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    def __str__(self):
        base = super().__str__()
        if self.process_type:
            return '{} ({})'.format(base, self.process_type)

        return '{}'.format(base)

    @classproperty
    def _updatable_attributes(cls):
        # pylint: disable=no-self-argument
        return super()._updatable_attributes + (
            cls.PROCESS_PAUSED_KEY,
            cls.CHECKPOINT_KEY,
            cls.EXCEPTION_KEY,
            cls.EXIT_MESSAGE_KEY,
            cls.EXIT_STATUS_KEY,
            cls.PROCESS_LABEL_KEY,
            cls.PROCESS_STATE_KEY,
            cls.PROCESS_STATUS_KEY,
        )

    @property
    def logger(self):
        """
        Get the logger of the Calculation object, so that it also logs to the DB.

        :return: LoggerAdapter object, that works like a logger, but also has the 'extra' embedded
        """
        from aiida.orm.utils.log import create_logger_adapter
        return create_logger_adapter(self._logger, self)

    def get_builder_restart(self):
        """Return a `ProcessBuilder` that is ready to relaunch the process that created this node.

        The process class will be set based on the `process_type` of this node and the inputs of the builder will be
        prepopulated with the inputs registered for this node. This functionality is very useful if a process has
        completed and you want to relaunch it with slightly different inputs.

        :return: `~aiida.engine.processes.builder.ProcessBuilder` instance
        """
        builder = self.process_class.get_builder()
        builder._update(self.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK)).nested())  # pylint: disable=protected-access

        return builder

    @property
    def process_class(self):
        """Return the process class that was used to create this node.

        :return: `Process` class
        :raises ValueError: if no process type is defined, it is an invalid process type string or cannot be resolved
            to load the corresponding class
        """
        from aiida.common import exceptions
        from aiida.plugins.entry_point import load_entry_point_from_string

        if not self.process_type:
            raise ValueError('no process type for CalcJobNode<{}>: cannot recreate process class'.format(self.pk))

        try:
            process_class = load_entry_point_from_string(self.process_type)
        except exceptions.EntryPointError as exception:
            raise ValueError(
                'could not load process class for entry point {} for CalcJobNode<{}>: {}'.format(
                    self.pk, self.process_type, exception
                )
            )
        except ValueError:
            try:
                import importlib
                module_name, class_name = self.process_type.rsplit('.', 1)
                module = importlib.import_module(module_name)
                process_class = getattr(module, class_name)
            except (ValueError, ImportError):
                raise ValueError(
                    'could not load process class CalcJobNode<{}> given its `process_type`: {}'.format(
                        self.pk, self.process_type
                    )
                )

        return process_class

    def set_process_type(self, process_type_string):
        """
        Set the process type string.

        :param process_type: the process type string identifying the class using this process node as storage.
        """
        self.process_type = process_type_string

    @property
    def process_label(self):
        """
        Return the process label

        :returns: the process label
        """
        return self.get_attribute(self.PROCESS_LABEL_KEY, None)

    def set_process_label(self, label):
        """
        Set the process label

        :param label: process label string
        """
        self.set_attribute(self.PROCESS_LABEL_KEY, label)

    @property
    def process_state(self):
        """
        Return the process state

        :returns: the process state instance of ProcessState enum
        """
        state = self.get_attribute(self.PROCESS_STATE_KEY, None)

        if state is None:
            return state

        return ProcessState(state)

    def set_process_state(self, state):
        """
        Set the process state

        :param state: value or instance of ProcessState enum
        """
        if isinstance(state, ProcessState):
            state = state.value
        return self.set_attribute(self.PROCESS_STATE_KEY, state)

    @property
    def process_status(self):
        """
        Return the process status

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed

        :returns: the process status
        """
        return self.get_attribute(self.PROCESS_STATUS_KEY, None)

    def set_process_status(self, status):
        """
        Set the process status

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed.
        If status is None, the corresponding attribute will be deleted.

        :param status: string process status
        """
        if status is None:
            try:
                self.delete_attribute(self.PROCESS_STATUS_KEY)
            except AttributeError:
                pass
            return None

        if not isinstance(status, str):
            raise TypeError('process status should be a string')

        return self.set_attribute(self.PROCESS_STATUS_KEY, status)

    @property
    def is_terminated(self):
        """
        Return whether the process has terminated

        Terminated means that the process has reached any terminal state.

        :return: True if the process has terminated, False otherwise
        :rtype: bool
        """
        return self.is_excepted or self.is_finished or self.is_killed

    @property
    def is_excepted(self):
        """
        Return whether the process has excepted

        Excepted means that during execution of the process, an exception was raised that was not caught.

        :return: True if during execution of the process an exception occurred, False otherwise
        :rtype: bool
        """
        return self.process_state == ProcessState.EXCEPTED

    @property
    def is_killed(self):
        """
        Return whether the process was killed

        Killed means the process was killed directly by the user or by the calling process being killed.

        :return: True if the process was killed, False otherwise
        :rtype: bool
        """
        return self.process_state == ProcessState.KILLED

    @property
    def is_finished(self):
        """
        Return whether the process has finished

        Finished means that the process reached a terminal state nominally.
        Note that this does not necessarily mean successfully, but there were no exceptions and it was not killed.

        :return: True if the process has finished, False otherwise
        :rtype: bool
        """
        return self.process_state == ProcessState.FINISHED

    @property
    def is_finished_ok(self):
        """
        Return whether the process has finished successfully

        Finished successfully means that it terminated nominally and had a zero exit status.

        :return: True if the process has finished successfully, False otherwise
        :rtype: bool
        """
        return self.is_finished and self.exit_status == 0

    @property
    def is_failed(self):
        """
        Return whether the process has failed

        Failed means that the process terminated nominally but it had a non-zero exit status.

        :return: True if the process has failed, False otherwise
        :rtype: bool
        """
        return self.is_finished and self.exit_status != 0

    @property
    def exit_status(self):
        """
        Return the exit status of the process

        :returns: the exit status, an integer exit code or None
        """
        return self.get_attribute(self.EXIT_STATUS_KEY, None)

    def set_exit_status(self, status):
        """
        Set the exit status of the process

        :param state: an integer exit code or None, which will be interpreted as zero
        """
        if status is None:
            status = 0

        if isinstance(status, enum.Enum):
            status = status.value

        if not isinstance(status, int):
            raise ValueError('exit status has to be an integer, got {}'.format(status))

        return self.set_attribute(self.EXIT_STATUS_KEY, status)

    @property
    def exit_message(self):
        """
        Return the exit message of the process

        :returns: the exit message
        """
        return self.get_attribute(self.EXIT_MESSAGE_KEY, None)

    def set_exit_message(self, message):
        """
        Set the exit message of the process, if None nothing will be done

        :param message: a string message
        """
        if message is None:
            return None

        if not isinstance(message, str):
            raise ValueError('exit message has to be a string type, got {}'.format(type(message)))

        return self.set_attribute(self.EXIT_MESSAGE_KEY, message)

    @property
    def exception(self):
        """
        Return the exception of the process or None if the process is not excepted.

        If the process is marked as excepted yet there is no exception attribute, an empty string will be returned.

        :returns: the exception message or None
        """
        if self.is_excepted:
            return self.get_attribute(self.EXCEPTION_KEY, '')

        return None

    def set_exception(self, exception):
        """
        Set the exception of the process

        :param exception: the exception message
        """
        if not isinstance(exception, str):
            raise ValueError('exception message has to be a string type, got {}'.format(type(exception)))

        return self.set_attribute(self.EXCEPTION_KEY, exception)

    @property
    def checkpoint(self):
        """
        Return the checkpoint bundle set for the process

        :returns: checkpoint bundle if it exists, None otherwise
        """
        return self.get_attribute(self.CHECKPOINT_KEY, None)

    def set_checkpoint(self, checkpoint):
        """
        Set the checkpoint bundle set for the process

        :param state: string representation of the stepper state info
        """
        return self.set_attribute(self.CHECKPOINT_KEY, checkpoint)

    def delete_checkpoint(self):
        """
        Delete the checkpoint bundle set for the process
        """
        try:
            self.delete_attribute(self.CHECKPOINT_KEY)
        except AttributeError:
            pass

    @property
    def paused(self):
        """
        Return whether the process is paused

        :returns: True if the Calculation is marked as paused, False otherwise
        """
        return self.get_attribute(self.PROCESS_PAUSED_KEY, False)

    def pause(self):
        """
        Mark the process as paused by setting the corresponding attribute.

        This serves only to reflect that the corresponding Process is paused and so this method should not be called
        by anyone but the Process instance itself.
        """
        return self.set_attribute(self.PROCESS_PAUSED_KEY, True)

    def unpause(self):
        """
        Mark the process as unpaused by removing the corresponding attribute.

        This serves only to reflect that the corresponding Process is unpaused and so this method should not be called
        by anyone but the Process instance itself.
        """
        try:
            self.delete_attribute(self.PROCESS_PAUSED_KEY)
        except AttributeError:
            pass

    @property
    def called(self):
        """
        Return a list of nodes that the process called

        :returns: list of process nodes called by this process
        """
        return self.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all_nodes()

    @property
    def called_descendants(self):
        """
        Return a list of all nodes that have been called downstream of this process

        This will recursively find all the called processes for this process and its children.
        """
        descendants = []

        for descendant in self.called:
            descendants.append(descendant)
            descendants.extend(descendant.called_descendants)

        return descendants

    @property
    def caller(self):
        """
        Return the process node that called this process node, or None if it does not have a caller

        :returns: process node that called this process node instance or None
        """
        try:
            caller = self.get_incoming(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).one().node
        except ValueError:
            return None
        else:
            return caller

    def validate_incoming(self, source, link_type, link_label):
        """Validate adding a link of the given type from a given node to ourself.

        Adding an input link to a `ProcessNode` once it is stored is illegal because this should be taken care of
        by the engine in one go. If a link is being added after the node is stored, it is most likely not by the engine
        and it should not be allowed.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super().validate_incoming(source, link_type, link_label)
        if self.is_stored:
            raise ValueError('attempted to add an input link after the process node was already stored.')

    @property
    def is_valid_cache(self):
        """
        Return whether the node is valid for caching

        :returns: True if this process node is valid to be used for caching, False otherwise
        """
        if not (super().is_valid_cache and self.is_finished):
            return False
        try:
            process_class = self.process_class
        except ValueError as exc:
            self.logger.warning(
                "Not considering {} for caching, '{!r}' when accessing its process class.".format(self, exc)
            )
            return False
        # For process functions, the `process_class` does not have an
        # is_valid_cache attribute
        try:
            is_valid_cache_func = process_class.is_valid_cache
        except AttributeError:
            return True

        return is_valid_cache_func(self)

    def _get_objects_to_hash(self):
        """
        Return a list of objects which should be included in the hash.
        """
        res = super()._get_objects_to_hash()
        res.append({
            entry.link_label: entry.node.get_hash()
            for entry in self.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK))
            if entry.link_label not in self._hash_ignored_inputs
        })
        return res

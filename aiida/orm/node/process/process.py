# -*- coding: utf-8 -*-
# pylint: disable=no-self-argument
"""ORM class for ProcessNode."""
from __future__ import absolute_import
import enum
import logging
import six

from plumpy import ProcessState

from aiida.common.links import LinkType
from aiida.common.utils import classproperty
from aiida.orm.mixins import Sealable
from aiida.plugins.entry_point import get_entry_point_string_from_class

from aiida.orm.implementation import Node

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
    PROCESS_LABEL_KEY = '_process_label'
    PROCESS_PAUSED_KEY = 'paused'
    PROCESS_STATE_KEY = 'process_state'
    PROCESS_STATUS_KEY = 'process_status'

    # The link_type might not be correct while the object is being created.
    _hash_ignored_inputs = ['CALL']

    # Specific sub classes should be marked as cacheable when appropriate
    _cacheable = False

    @classproperty
    def _updatable_attributes(cls):
        return super(ProcessNode, cls)._updatable_attributes + (
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
        from aiida.common.log import get_dblogger_extra
        return logging.LoggerAdapter(logger=self._logger, extra=get_dblogger_extra(self))

    def _set_process_type(self, process_class):
        """
        Set the process type

        :param process_class: the process class using this process node as storage
        """
        class_module = process_class.__module__
        class_name = process_class.__name__

        # If the process is a registered plugin the corresponding entry point will be used as process type
        process_type = get_entry_point_string_from_class(class_module, class_name)

        # If no entry point was found, default to fully qualified path name
        if process_type is None:
            self.dbnode.process_type = '{}.{}'.format(class_module, class_name)
        else:
            self.dbnode.process_type = process_type

    @property
    def process_label(self):
        """
        Return the process label

        :returns: the process label
        """
        return self.get_attr(self.PROCESS_LABEL_KEY, None)

    def _set_process_label(self, label):
        """
        Set the process label

        :param label: process label string
        """
        self._set_attr(self.PROCESS_LABEL_KEY, label)

    @property
    def process_state(self):
        """
        Return the process state

        :returns: the process state instance of ProcessState enum
        """
        state = self.get_attr(self.PROCESS_STATE_KEY, None)

        if state is None:
            return state

        return ProcessState(state)

    def _set_process_state(self, state):
        """
        Set the process state

        :param state: value or instance of ProcessState enum
        """
        if isinstance(state, ProcessState):
            state = state.value
        return self._set_attr(self.PROCESS_STATE_KEY, state)

    @property
    def process_status(self):
        """
        Return the process status

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed

        :returns: the process status
        """
        return self.get_attr(self.PROCESS_STATUS_KEY, None)

    def _set_process_status(self, status):
        """
        Set the process status

        The process status is a generic status message e.g. the reason it might be paused or when it is being killed.
        If status is None, the corresponding attribute will be deleted.

        :param status: string process status
        """
        if status is None:
            try:
                self._del_attr(self.PROCESS_STATUS_KEY)
            except AttributeError:
                pass
            return None

        if not isinstance(status, six.string_types):
            raise TypeError('process status should be a string')

        return self._set_attr(self.PROCESS_STATUS_KEY, status)

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
        return self.get_attr(self.EXIT_STATUS_KEY, None)

    def _set_exit_status(self, status):
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

        return self._set_attr(self.EXIT_STATUS_KEY, status)

    @property
    def exit_message(self):
        """
        Return the exit message of the process

        :returns: the exit message
        """
        return self.get_attr(self.EXIT_MESSAGE_KEY, None)

    def _set_exit_message(self, message):
        """
        Set the exit message of the process, if None nothing will be done

        :param message: a string message
        """
        if message is None:
            return None

        if not isinstance(message, six.string_types):
            raise ValueError('exit message has to be a string type, got {}'.format(type(message)))

        return self._set_attr(self.EXIT_MESSAGE_KEY, message)

    @property
    def exception(self):
        """
        Return the exception of the process or None if the process is not excepted.

        If the process is marked as excepted yet there is no exception attribute, an empty string will be returned.

        :returns: the exception message or None
        """
        if self.is_excepted:
            return self.get_attr(self.EXCEPTION_KEY, '')

        return None

    def _set_exception(self, exception):
        """
        Set the exception of the process

        :param exception: the exception message
        """
        if not isinstance(exception, six.string_types):
            raise ValueError('exception message has to be a string type, got {}'.format(type(exception)))

        return self._set_attr(self.EXCEPTION_KEY, exception)

    @property
    def checkpoint(self):
        """
        Return the checkpoint bundle set for the process

        :returns: checkpoint bundle if it exists, None otherwise
        """
        return self.get_attr(self.CHECKPOINT_KEY, None)

    def set_checkpoint(self, checkpoint):
        """
        Set the checkpoint bundle set for the process

        :param state: string representation of the stepper state info
        """
        return self._set_attr(self.CHECKPOINT_KEY, checkpoint)

    def del_checkpoint(self):
        """
        Delete the checkpoint bundle set for the process
        """
        try:
            self._del_attr(self.CHECKPOINT_KEY)
        except AttributeError:
            pass

    @property
    def paused(self):
        """
        Return whether the process is paused

        :returns: True if the Calculation is marked as paused, False otherwise
        """
        return self.get_attr(self.PROCESS_PAUSED_KEY, False)

    def pause(self):
        """
        Mark the process as paused by setting the corresponding attribute.

        This serves only to reflect that the corresponding Process is paused and so this method should not be called
        by anyone but the Process instance itself.
        """
        return self._set_attr(self.PROCESS_PAUSED_KEY, True)

    def unpause(self):
        """
        Mark the process as unpaused by removing the corresponding attribute.

        This serves only to reflect that the corresponding Process is unpaused and so this method should not be called
        by anyone but the Process instance itself.
        """
        try:
            self._del_attr(self.PROCESS_PAUSED_KEY)
        except AttributeError:
            pass

    @property
    def called(self):
        """
        Return a list of nodes that the process called

        :returns: list of process nodes called by this process
        """
        return self.get_outputs(link_type=LinkType.CALL)

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
    def called_by(self):
        """
        Return the process node that called this process node, or None if it does not have a caller

        :returns: process node that called this process node instance or None
        """
        called_by = self.get_inputs(link_type=LinkType.CALL)
        if called_by:
            return called_by[0]

        return None

    def _linking_as_output(self, dest, link_type):
        """
        Link this process node to another node with a given link type.

        :param dest: a `Node` instance
        :raise: ValueError if a link from self to `dest` is not allowed.
        """
        from aiida.orm.data import Data

        if link_type is LinkType.CREATE or link_type is LinkType.RETURN:
            if not isinstance(dest, Data):
                raise ValueError('The output of a process node can only be a data node')
        elif link_type is LinkType.CALL:
            if not isinstance(dest, ProcessNode):
                raise ValueError('Call links can only link two process nodes: {}'.format(type(dest)))
        else:
            raise ValueError('a process node cannot have links of type {} as output'.format(link_type))

        return super(ProcessNode, self)._linking_as_output(dest, link_type)

    def add_link_from(self, src, label=None, link_type=LinkType.INPUT):
        """
        Add a link from another node.

        :param src: node to add the link from
        :param str label: name of the link, default is None
        :param link_type: the type of link, must be one of the enum values form :class:`~aiida.common.links.LinkType`
        """
        from aiida.orm.data import Data

        if link_type is LinkType.INPUT:
            if not isinstance(src, Data):
                raise ValueError('Nodes entering processes as input link can only be of type data')
        elif link_type is LinkType.CALL:
            if not isinstance(src, ProcessNode):
                raise ValueError('Call links can only link two process nodes: {}'.format(type(src)))
        else:
            raise ValueError('Process node cannot have links of type {} as input'.format(link_type))

        return super(ProcessNode, self).add_link_from(src, label, link_type)

    def _is_valid_cache(self):
        """
        Return whether the node is valid for caching

        :returns: True if this process node is valid to be used for caching, False otherwise
        """
        return super(ProcessNode, self)._is_valid_cache() and self.is_finished_ok

    def _get_objects_to_hash(self):
        """
        Return a list of objects which should be included in the hash.
        """
        res = super(ProcessNode, self)._get_objects_to_hash()
        res.append({
            key: value.get_hash()
            for key, value in self.get_inputs_dict(link_type=LinkType.INPUT).items()
            if key not in self._hash_ignored_inputs
        })
        return res

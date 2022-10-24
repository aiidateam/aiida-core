# -*- coding: utf-8 -*-
"""A sub class of ``plumpy.ProcessLauncher`` to launch a ``Process``."""
import asyncio
import logging
import traceback

import kiwipy
import plumpy

LOGGER = logging.getLogger(__name__)

__all__ = ('ProcessLauncher',)


class ProcessLauncher(plumpy.ProcessLauncher):
    """A sub class of :class:`plumpy.ProcessLauncher` to launch a ``Process``.

    It overrides the _continue method to make sure the node corresponding to the task can be loaded and
    that if it is already marked as terminated, it is not continued but the future is reconstructed and returned
    """

    @staticmethod
    def handle_continue_exception(node, exception, message):
        """Handle exception raised in `_continue` call.

        If the process state of the node has not yet been put to excepted, the exception was raised before the process
        instance could be reconstructed, for example when the process class could not be loaded, thereby circumventing
        the exception handling of the state machine. Raising this exception will then acknowledge the process task with
        RabbitMQ leaving an uncleaned node in the `CREATED` state for ever. Therefore we have to perform the node
        cleaning manually.

        :param exception: the exception object
        :param message: string message to use for the log message
        """
        from aiida.engine import ProcessState

        if not node.is_excepted and not node.is_sealed:
            node.logger.exception(message)
            node.set_exception(''.join(traceback.format_exception(type(exception), exception, None)).rstrip())
            node.set_process_state(ProcessState.EXCEPTED)
            node.seal()

    async def _continue(self, communicator, pid, nowait, tag=None):
        """Continue the task.

        Note that the task may already have been completed, as indicated from the corresponding the node, in which
        case it is not continued, but the corresponding future is reconstructed and returned. This scenario may
        occur when the Process was already completed by another worker that however failed to send the acknowledgment.

        :param communicator: the communicator that called this method
        :param pid: the pid of the process to continue
        :param nowait: if True don't wait for the process to finish, just return the pid, otherwise wait and
            return the results
        :param tag: the tag of the checkpoint to continue from
        """
        from aiida.common import exceptions
        from aiida.engine.exceptions import PastException
        from aiida.orm import Data, load_node
        from aiida.orm.utils import serialize

        try:
            node = load_node(pk=pid)
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            # In this case, the process node corresponding to the process id, cannot be resolved uniquely or does not
            # exist. The latter being the most common case, where someone deleted the node, before the process was
            # properly terminated. Since the node is never coming back and so the process will never be able to continue
            # we raise `Return` instead of `TaskRejected` because the latter would cause the task to be resent and start
            # to ping-pong between RabbitMQ and the daemon workers.
            LOGGER.exception('Cannot continue process<%d>', pid)
            return False

        if node.is_terminated:

            LOGGER.info('not continuing process<%d> which is already terminated with state %s', pid, node.process_state)

            future = kiwipy.Future()

            if node.is_finished:
                future.set_result({
                    entry.link_label: entry.node for entry in node.base.links.get_outgoing(node_class=Data)
                })
            elif node.is_excepted:
                future.set_exception(PastException(node.exception))
            elif node.is_killed:
                future.set_exception(plumpy.KilledError())

            return future.result()

        try:
            result = await super()._continue(communicator, pid, nowait, tag)
        except ImportError as exception:
            message = 'the class of the process could not be imported.'
            self.handle_continue_exception(node, exception, message)
            raise
        except kiwipy.DuplicateSubscriberIdentifier:
            # This happens when the current worker has already subscribed itself with this process identifier. The call
            # to ``_continue`` will call ``Process.init`` which will add RPC and broadcast subscribers. ``kiwipy`` and
            # ``aiormq`` further down keep track of processes that are already subscribed and if subscribed again, a
            # ``DuplicateSubscriberIdentifier`` is raised. Possible reasons for the worker receiving a process task that
            # it already has, include:
            #
            #  1. The user mistakenly recreates the corresponding task, thinking the original task was lost.
            #  2. RabbitMQ requeues the task because the daemon worker lost its connection or did not respond to the
            #     heartbeat in time, and the task is sent to the same worker once it regains connection.
            #
            # Here we assume that the existence of another subscriber indicates that the process is still being run by
            # this worker. We thus ignore the request to have the worker take it on again and acknowledge the current
            # task (`return False`). If our assumption was wrong and the original task was no longer being worked on,
            # the user can resubmit the task once the list of subscribers of the process has been cleared. Note: In the
            # second case we are deleting the *original* task, and once the worker finishes running the process there
            # won't be a task in RabbitMQ to acknowledge anymore. This, however, is silently ignored.
            #
            # Note: the exception is raised by ``kiwipy`` based on an internal cache it and ``aiormq`` keep of the
            # current subscribers. This means that this will only occur when the tasks is resent to the *same* daemon
            # worker. If another worker were to receive it, no exception would be raised as the check is client and not
            # server based.
            LOGGER.exception(
                'A subscriber with the process id<%d> already exists, which most likely means this worker is already '
                'working on it and this task was sent as a duplicate by mistake. Deleting the task now.', pid
            )
            return False
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            # note this is only required in python<=3.7,
            # where asyncio.CancelledError inherits from Exception
            raise
        except Exception as exception:
            message = 'failed to recreate the process instance in order to continue it.'
            self.handle_continue_exception(node, exception, message)
            raise

        # Ensure that the result is serialized such that communication thread won't have to do database operations
        try:
            serialized = serialize.serialize(result)
        except Exception:
            LOGGER.exception('failed to serialize the result for process<%d>', pid)
            raise

        return serialized

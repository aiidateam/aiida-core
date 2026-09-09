"""Utilites for RabbitMQ."""

from __future__ import annotations

import asyncio
import collections.abc
import functools
import inspect
import os
import socket
import traceback
from collections.abc import Callable
from types import TracebackType
from typing import Any

from aiida.brokers import exceptions
from aiida.brokers.rabbitmq import defaults

# The key used in messages to give information about the host that sent a message
HOST_KEY = 'host'
HOSTNAME_KEY = 'hostname'
PID_KEY = 'pid'
RESULT_KEY = 'result'
EXCEPTION_KEY = 'exception'
CANCELLED_KEY = 'cancelled'
PENDING_KEY = 'pending'


def get_rmq_url(
    protocol: str | None = None,
    username: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | None = None,
    virtual_host: str | None = None,
    **kwargs: Any,
) -> str:
    """Return the URL to connect to RabbitMQ.

    .. note::

        The default of the ``host`` is set to ``127.0.0.1`` instead of ``localhost`` because on some computers localhost
        resolves first to IPv6 with address ::1 and if RMQ is not running on IPv6 one gets an annoying warning. For more
        info see: https://github.com/aiidateam/aiida-core/issues/1142

    :param protocol: the protocol to use, `amqp` or `amqps`.
    :param username: the username for authentication.
    :param password: the password for authentication.
    :param host: the hostname of the RabbitMQ server.
    :param port: the port of the RabbitMQ server.
    :param virtual_host: the virtual host to connect to.
    :param kwargs: remaining keyword arguments that will be encoded as query parameters.
    :returns: the connection URL string.
    """
    from urllib.parse import quote, urlencode, urlunparse

    if 'heartbeat' not in kwargs:
        kwargs['heartbeat'] = defaults.BROKER_DEFAULTS.heartbeat

    scheme = protocol or defaults.BROKER_DEFAULTS.protocol
    netloc = '{username}:{password}@{host}:{port}'.format(
        username=quote(username or defaults.BROKER_DEFAULTS.username, safe=''),
        password=quote(password or defaults.BROKER_DEFAULTS.password, safe=''),
        host=host or defaults.BROKER_DEFAULTS.host,
        port=port or defaults.BROKER_DEFAULTS.port,
    )
    path = virtual_host or defaults.BROKER_DEFAULTS.virtual_host
    parameters = ''
    query = urlencode(kwargs)
    fragment = ''

    # The virtual host is optional but if it is specified it needs to start with a forward slash. If the virtual host
    # itself contains forward slashes, they need to be encoded.
    if path and not path.startswith('/'):
        path = f'/{path}'

    return urlunparse((scheme, netloc, path, parameters, query, fragment))  # type: ignore[no-any-return]


def get_launch_queue_name(prefix: str | None = None) -> str:
    """Return the launch queue name with an optional prefix.

    :returns: launch queue name
    """
    if prefix is not None:
        return f'{prefix}.{defaults.LAUNCH_QUEUE}'

    return defaults.LAUNCH_QUEUE


def get_message_exchange_name(prefix: str) -> str:
    """Return the message exchange name for a given prefix.

    :returns: message exchange name
    """
    return f'{prefix}.{defaults.MESSAGE_EXCHANGE}'


def get_task_exchange_name(prefix: str) -> str:
    """Return the task exchange name for a given prefix.

    :returns: task exchange name
    """
    return f'{prefix}.{defaults.TASK_EXCHANGE}'


def get_host_info() -> dict[str, Any]:
    """Return information about the current host."""
    return {'hostname': socket.gethostname(), 'pid': os.getpid()}


def add_host_info(msg: dict[str, Any]) -> None:
    """Add host information to a message in place."""
    if HOST_KEY in msg:
        error_msg = 'Host information key already exists in message'
        raise ValueError(error_msg)

    msg[HOST_KEY] = get_host_info()


def result_response(result: Any) -> dict[str, Any]:
    """Create a result response dictionary."""
    return {RESULT_KEY: result}


def exception_response(exception: Exception, trace: TracebackType | None = None) -> dict[str, Any]:
    """Create an exception response dictionary.

    :param exception: The exception to encode.
    :param trace: Optional traceback.
    """
    msg = str(exception)
    if trace is not None:
        msg += f'\n{"".join(traceback.format_tb(trace)[0])}'
    return {EXCEPTION_KEY: msg}


def cancelled_response(msg: Any = None) -> dict[str, Any]:
    """Create a cancelled response dictionary."""
    return {CANCELLED_KEY: msg}


def pending_response(msg: Any = None) -> dict[str, Any]:
    """Create a pending response dictionary."""
    return {PENDING_KEY: msg}


def response_result(response: dict[str, Any]) -> Any:
    """Return the result of a response message, raising if it contains an exception."""
    future: asyncio.Future[Any] = asyncio.Future()
    response_to_future(response, future)
    return future.result()


def response_to_future(response: Any, future: asyncio.Future[Any] | None = None) -> asyncio.Future[Any]:
    """Take a response message and set the appropriate value on the given future."""
    if not isinstance(response, collections.abc.Mapping):
        msg = 'Response must be a mapping'
        raise TypeError(msg)

    if future is None:
        future = asyncio.Future[Any]()

    if CANCELLED_KEY in response:
        future.cancel()
    elif EXCEPTION_KEY in response:
        future.set_exception(exceptions.RemoteException(response[EXCEPTION_KEY]))
    elif RESULT_KEY in response:
        future.set_result(response[RESULT_KEY])
    elif PENDING_KEY in response:
        future.set_result(asyncio.Future())
    else:
        msg = f"Unknown response type '{response}'"
        raise ValueError(msg)

    return future


def future_to_response(future: asyncio.Future[Any]) -> dict[str, Any]:
    """Convert a future to a response dictionary."""
    if future.cancelled():
        return cancelled_response()
    try:
        return result_response(future.result())
    except Exception as exception:  # pylint: disable=broad-except
        return exception_response(exception)


def ensure_coroutine(coro_or_fn: Any) -> Callable[..., Any]:
    """Wrap a sync callable so it can be awaited on the communicator event loop."""
    if inspect.iscoroutinefunction(coro_or_fn):
        coroutine_fn: Callable[..., Any] = coro_or_fn
        return coroutine_fn
    if callable(coro_or_fn):
        if inspect.isclass(coro_or_fn):
            coro_or_fn = coro_or_fn.__call__

        @functools.wraps(coro_or_fn)
        async def wrap(*args: Any, **kwargs: Any) -> Any:
            return coro_or_fn(*args, **kwargs)

        wrapped: Callable[..., Any] = wrap
        return wrapped

    msg = 'coro_or_fn must be a callable'
    raise TypeError(msg)

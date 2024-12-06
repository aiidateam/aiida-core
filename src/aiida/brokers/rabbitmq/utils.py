"""Utilites for RabbitMQ."""

from . import defaults

__all__ = ('get_launch_queue_name', 'get_message_exchange_name', 'get_rmq_url', 'get_task_exchange_name')


def get_rmq_url(protocol=None, username=None, password=None, host=None, port=None, virtual_host=None, **kwargs):
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
    from urllib.parse import urlencode, urlunparse

    if 'heartbeat' not in kwargs:
        kwargs['heartbeat'] = defaults.BROKER_DEFAULTS.heartbeat

    scheme = protocol or defaults.BROKER_DEFAULTS.protocol
    netloc = '{username}:{password}@{host}:{port}'.format(
        username=username or defaults.BROKER_DEFAULTS.username,
        password=password or defaults.BROKER_DEFAULTS.password,
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

    return urlunparse((scheme, netloc, path, parameters, query, fragment))


def get_launch_queue_name(prefix=None):
    """Return the launch queue name with an optional prefix.

    :returns: launch queue name
    """
    if prefix is not None:
        return f'{prefix}.{defaults.LAUNCH_QUEUE}'

    return defaults.LAUNCH_QUEUE


def get_message_exchange_name(prefix):
    """Return the message exchange name for a given prefix.

    :returns: message exchange name
    """
    return f'{prefix}.{defaults.MESSAGE_EXCHANGE}'


def get_task_exchange_name(prefix):
    """Return the task exchange name for a given prefix.

    :returns: task exchange name
    """
    return f'{prefix}.{defaults.TASK_EXCHANGE}'

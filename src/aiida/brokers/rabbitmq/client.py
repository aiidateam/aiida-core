"""Client for RabbitMQ Management HTTP API."""

from __future__ import annotations

import typing as t

from aiida.common.exceptions import AiidaException

if t.TYPE_CHECKING:
    import requests


class ManagementApiConnectionError(AiidaException):
    """Raised when no connection can be made to the management HTTP API."""


class RabbitmqManagementClient:
    """Client for RabbitMQ Management HTTP API.

    This requires the ``rabbitmq_management`` plugin (https://www.rabbitmq.com/management.html) to be enabled. Typically
    this is enabled by running ``rabbitmq-plugins enable rabbitmq_management``.
    """

    def __init__(self, username: str, password: str, hostname: str, virtual_host: str):
        """Construct a new instance.

        :param username: The username to authenticate with.
        :param password: The password to authenticate with.
        :param hostname: The hostname of the RabbitMQ server.
        :param virtual_host: The virtual host.
        """
        import requests

        self._username = username
        self._password = password
        self._hostname = hostname
        self._virtual_host = virtual_host
        self._authentication = requests.auth.HTTPBasicAuth(username, password)

    def format_url(self, url: str, url_params: dict[str, str] | None = None) -> str:
        """Format the complete URL from a partial resource path with placeholders.

        The base URL will be automatically prepended.

        :param url: The resource path with placeholders, e.g., ``queues/{virtual_host}/{queue}``.
        :param url_params: Dictionary with values for the placeholders in the ``url``. The ``virtual_host`` value is
            automatically inserted and should not be specified.
        :returns: The complete URL.
        """
        from urllib.parse import quote

        url_params = url_params or {}
        url_params['virtual_host'] = self._virtual_host if self._virtual_host else '/'
        url_params = {key: quote(value, safe='') for key, value in url_params.items()}
        return f'http://{self._hostname}:15672/api/{url.format(**url_params)}'

    def request(
        self,
        url: str,
        url_params: dict[str, str] | None = None,
        method: str = 'GET',
        params: dict[str, t.Any] | None = None,
    ) -> 'requests.Response':
        """Make a request.

        :param url: The resource path with placeholders, e.g., ``queues/{virtual_host}/{queue}``.
        :param url_params: Dictionary with values for the placeholders in the ``url``. The ``virtual_host`` value is
            automatically inserted and should not be specified.
        :param method: The HTTP method.
        :param params: Query parameters to add to the URL.
        :returns: The response of the request.
        :raises `ManagementApiConnectionError`: If connection to the API cannot be made.
        """
        import requests

        url = self.format_url(url, url_params)
        try:
            return requests.request(method, url, auth=self._authentication, params=params or {}, timeout=5)
        except requests.exceptions.ConnectionError as exception:
            raise ManagementApiConnectionError(
                'Could not connect to the management API. Make sure RabbitMQ is running and the management plugin is '
                'installed using `sudo rabbitmq-plugins enable rabbitmq_management`.'
            ) from exception

    @property
    def is_connected(self) -> bool:
        """Return whether the API server can be connected to.

        .. note:: Tries to reach the server at the ``/api/cluster-name`` end-point.

        :returns: ``True`` if the server can be reached, ``False`` otherwise.
        """
        try:
            self.request('cluster-name')
        except ManagementApiConnectionError:
            return False
        return True

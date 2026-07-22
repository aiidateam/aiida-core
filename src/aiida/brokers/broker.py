"""Interface for a message broker that facilitates communication with and between process runners."""

from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass

from aiida.common.lang import classproperty

JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | list['JsonValue'] | dict[str, 'JsonValue']
BrokerServiceStatus = dict[str, JsonValue]

if t.TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from aiida.manage.configuration.profile import Profile

# We intentionally do not expose all entities to public API, because we might change it later
__all__ = ('Broker',)


@dataclass(frozen=True)
class BrokerConfigField:
    """Metadata for a broker configuration field."""

    name: str
    prompt: str
    help: str
    default: t.Any
    param_type: str
    choices: tuple[str, ...] | None = None
    hide_input: bool = False
    expose_cli: bool = True
    """Whether the field is exposed as a CLI option. If ``False``, the default value is always used."""


class Broker(abc.ABC):
    """Interface for a message broker that facilitates communication with and between process runners."""

    ENTRY_POINT_GROUP = 'aiida.brokers'
    _config_fields: tuple[BrokerConfigField, ...] = ()

    @classproperty
    def ENTRY_POINT(cls) -> str:  # noqa: N802, N805
        """Return the entry point name of this broker class."""
        from aiida.plugins.entry_point import get_entry_point_from_class

        group, entry_point = get_entry_point_from_class(cls.__module__, cls.__name__)

        if group != cls.ENTRY_POINT_GROUP or entry_point is None:
            msg = f'could not determine entry point for `{cls.__name__}` in group `{cls.ENTRY_POINT_GROUP}`'
            raise RuntimeError(msg)

        return entry_point.name

    def __init__(self, profile: Profile) -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
        self._profile = profile

    @classmethod
    def get_default_config(cls) -> dict[str, t.Any]:
        """Return the default broker configuration derived from the declared config fields.

        :return: Mapping of configuration field names to their default values.
        """
        return {field.name: field.default for field in cls._config_fields}

    @classmethod
    def get_detected_config(cls, get_value: Callable[[str], t.Any]) -> dict[str, t.Any]:
        """Return detected configuration values for CLI defaults.

        The callable should return the current value for a config field name.

        :return: Mapping of configuration field names to detected values.
        """
        return {}

    @abc.abstractmethod
    def get_communicator(self) -> t.Any:
        """Return a communicator instance for the broker.

        :return: An instance of :class:`kiwipy.Communicator`.
        """

    @abc.abstractmethod
    def iterate_tasks(self) -> Iterator[t.Any]:
        """Return an iterator over the tasks in the launch queue.

        :return: Iterator over broker-specific task objects.
        """

    @abc.abstractmethod
    def check_service_reachable(self) -> bool:
        """Return whether the broker service is reachable from this client.

        :return: ``True`` if the broker service can be reached, ``False`` otherwise.
        """

    @abc.abstractmethod
    def probe_service_status(self) -> BrokerServiceStatus:
        """Return service status information for the broker.

        Retrieval failures should be captured in the returned status payload instead of raising.

        :return: Structured service status information.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Close broker resources held by this instance."""

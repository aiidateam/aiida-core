"""Interface for a message broker that facilitates communication with and between process runners."""

from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass

if t.TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from aiida.manage.configuration.profile import Profile

__all__ = ('Broker', 'BrokerConfigField')


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


class Broker(abc.ABC):
    """Interface for a message broker that facilitates communication with and between process runners."""

    _config_fields: tuple[BrokerConfigField, ...] = ()

    def __init__(self, profile: 'Profile') -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
        self._profile = profile

    @classmethod
    def get_detected_config(cls, get_value: 'Callable[[str], t.Any]') -> dict[str, t.Any]:
        """Return detected configuration values for CLI defaults.

        The callable should return the current value for a config field name.

        :return: Mapping of configuration field names to detected values.
        """
        return {}

    @abc.abstractmethod
    def get_communicator(self) -> t.Any:
        """Return an instance of :class:`kiwipy.Communicator`."""

    @abc.abstractmethod
    def iterate_tasks(self) -> Iterator[t.Any]:
        """Return an iterator over the tasks in the launch queue."""

    @abc.abstractmethod
    def close(self) -> None:
        """Close the broker."""

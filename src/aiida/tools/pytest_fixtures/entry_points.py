"""Fixtures to temporarily add and remove entry points."""

from __future__ import annotations

import typing as t

import importlib_metadata
import pytest


class EntryPointManager:
    """Manager to temporarily add or remove entry points."""

    def __init__(self, entry_points: importlib_metadata.EntryPoints):
        self.entry_points = entry_points

    def eps(self) -> importlib_metadata.EntryPoints:
        return self.entry_points

    def eps_select(self, group, name=None) -> importlib_metadata.EntryPoints:
        if name is None:
            return self.eps().select(group=group)
        return self.eps().select(group=group, name=name)

    @staticmethod
    def _validate_entry_point(entry_point_string: str | None, group: str | None, name: str | None) -> tuple[str, str]:
        """Validate the definition of the entry point.

        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        from aiida.common.lang import type_check
        from aiida.plugins import entry_point

        if entry_point_string is not None:
            try:
                group, name = entry_point.parse_entry_point_string(entry_point_string)
            except TypeError as exception:
                raise TypeError('`entry_point_string` should be a string when defined.') from exception
            except ValueError as exception:
                raise ValueError('invalid `entry_point_string` format, should `group:name`.') from exception

        if name is None or group is None:
            raise ValueError('neither `entry_point_string` is defined, nor `name` and `group`.')

        type_check(group, str)
        type_check(name, str)

        return group, name

    def add(
        self,
        value: type | str,
        entry_point_string: str | None = None,
        *,
        name: str | None = None,
        group: str | None = None,
    ) -> None:
        """Add an entry point.

        :param value: The class or function to register as entry point. The resource needs to be importable, so it can't
            be inlined. Alternatively, the fully qualified name can be passed as a string.
        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        if not isinstance(value, str):
            value = f'{value.__module__}:{value.__name__}'

        group, name = self._validate_entry_point(entry_point_string, group, name)
        entry_point = importlib_metadata.EntryPoint(name, value, group)
        self.entry_points = importlib_metadata.EntryPoints(self.entry_points + (entry_point,))

    def remove(
        self, entry_point_string: str | None = None, *, name: str | None = None, group: str | None = None
    ) -> None:
        """Remove an entry point.

        :param value: Entry point value, fully qualified import path name.
        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        group, name = self._validate_entry_point(entry_point_string, group, name)
        try:
            self.entry_points[name]
        except KeyError:
            raise KeyError(f'entry point `{name}` does not exist in group `{group}`.')
        self.entry_points = importlib_metadata.EntryPoints(
            (ep for ep in self.entry_points if not (ep.name == name and ep.group == group))
        )


@pytest.fixture
def entry_points(monkeypatch) -> t.Generator[EntryPointManager, None, None]:
    """Return an instance of the ``EntryPointManager`` which allows to temporarily add or remove entry points.

    This fixture monkey patches the entry point caches returned by the :func:`aiida.plugins.entry_point.eps` and
    :func:`aiida.plugins.entry_point.eps_select` functions to class methods of the ``EntryPointManager`` so that we can
    dynamically add and/or remove entry points.

    Usage::

        def test(entry_points):
            entry_points.add(SomeCalcJob, 'aiida.calculations:some.entry_point')
            # or, alternatively
            entry_points.add(SomeCalcJob, group='aiida.calculations', name='some.entry_point')
    """
    from aiida.plugins import entry_point

    # Note: a deepcopy is not needed here as ``eps()`` returns an immutable ``EntryPoints`` tuple type.
    epm = EntryPointManager(entry_point.eps())
    monkeypatch.setattr(entry_point, 'eps', epm.eps)
    monkeypatch.setattr(entry_point, 'eps_select', epm.eps_select)
    yield epm

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin to store a reference to an entry point."""

from __future__ import annotations

import typing as t

from importlib_metadata import EntryPoint
from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.exceptions import EntryPointError
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.decorators.attributes import attribute
from aiida.orm.nodes.data.data import Data
from aiida.plugins.entry_point import get_entry_point
from aiida.plugins.utils import PluginVersionProvider

__all__ = ('EntryPointData',)

LOGGER = AIIDA_LOGGER.getChild('entry_point')
VERSION_PROVIDER = PluginVersionProvider()  # type: ignore[no-untyped-call]


class EntryPointData(Data):
    """Data plugin to store a reference to an entry point."""

    KEY_ATTRIBUTES_NAME: str = 'name'
    """Attribute key that stores the ``name`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_GROUP: str = 'group'
    """Attribute key that stores the ``group`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_VALUE: str = 'value'
    """Attribute key that stores the ``value`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_MODULE: str = 'module'
    """Attribute key that stores the ``module`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_ATTR: str = 'attr'
    """Attribute key that stores the ``attr`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_EXTRAS: str = 'extras'
    """Attribute key that stores the ``extras`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_VERSION: str = 'version'
    """Attribute key that stores the version of the package that provided the entry point, if available."""

    @classmethod
    def from_entry_point(cls, entry_point: EntryPoint, **kwargs: t.Any) -> Self:
        """Construct a new instance from an entry point.

        :param entry_point: The entry point to wrap.
        :param kwargs: Additional keyword arguments forwarded to :class:`~aiida.orm.nodes.data.data.Data`.
        :raises TypeError: If the ``entry_point`` is not an instance of ``EntryPoint``.
        :raises ValueError: If the ``entry_point`` is inconsistent, i.e., its ``name`` and ``group`` do not correspond
            to an existing entry point or it corresponds to a different entry point.
        """
        if not isinstance(entry_point, EntryPoint):
            msg = f'entry_point should be of type `EntryPoint`, got: {type(entry_point)}'  # type: ignore[unreachable]
            raise TypeError(msg)

        loaded = cls._validate_entry_point(entry_point)

        node = cls(**kwargs)
        node._set_entry_point(entry_point, loaded)

        return node

    @classmethod
    def from_name(cls, group: str, name: str, **kwargs: t.Any) -> Self:
        """Construct a new instance from the group and name of a registered entry point.

        :param group: The group of the entry point.
        :param name: The name of the entry point.
        :param kwargs: Additional keyword arguments forwarded to :class:`~aiida.orm.nodes.data.data.Data`.
        :raises ValueError: If the ``name`` and ``group`` cannot be resolved to an entry point that can be loaded.
        """
        try:
            entry_point = get_entry_point(group, name)
        except EntryPointError as exception:
            msg = f'entry point with group `{group}` and name `{name}` does not exist.'
            raise ValueError(msg) from exception

        return cls.from_entry_point(entry_point, **kwargs)

    @attribute(readonly=True)
    def name(self) -> str:
        """The name of the wrapped entry point."""
        return t.cast(str, self.base.attributes.get(self.KEY_ATTRIBUTES_NAME))

    @attribute(readonly=True)
    def group(self) -> str:
        """The group of the wrapped entry point."""
        return t.cast(str, self.base.attributes.get(self.KEY_ATTRIBUTES_GROUP))

    @attribute(readonly=True)
    def value(self) -> str:
        """The value of the wrapped entry point."""
        return t.cast(str, self.base.attributes.get(self.KEY_ATTRIBUTES_VALUE))

    @attribute(readonly=True)
    def module(self) -> str:
        """The module of the wrapped entry point."""
        return t.cast(str, self.base.attributes.get(self.KEY_ATTRIBUTES_MODULE))

    @attribute(readonly=True)
    def attr(self) -> str | None:
        """The attribute of the wrapped entry point."""
        return t.cast(str | None, self.base.attributes.get(self.KEY_ATTRIBUTES_ATTR, None))

    @attribute(readonly=True)
    def extras(self) -> list[str]:
        """The extras of the wrapped entry point."""
        return t.cast(list[str], self.base.attributes.get(self.KEY_ATTRIBUTES_EXTRAS))

    @attribute(readonly=True)
    def version(self) -> str | None:
        """The version of the package that provided the entry point, if available."""
        return t.cast(str | None, self.base.attributes.get(self.KEY_ATTRIBUTES_VERSION, None))

    def load(self) -> t.Any:
        """Load and return the wrapped entry point.

        :returns: The object that the entry point refers to.
        :raises EntryPointError: If the entry point does not exist or cannot be loaded.
        """
        entry_point = EntryPoint(
            name=self.name,
            group=self.group,
            value=self.value,
        )
        return entry_point.load()  # type: ignore[no-untyped-call]

    def _set_entry_point(self, entry_point: EntryPoint, loaded: t.Any) -> None:
        """Set the attributes describing an entry point."""
        attributes = {
            self.KEY_ATTRIBUTES_NAME: entry_point.name,
            self.KEY_ATTRIBUTES_GROUP: entry_point.group,
            self.KEY_ATTRIBUTES_VALUE: entry_point.value,
            self.KEY_ATTRIBUTES_MODULE: entry_point.module,
            self.KEY_ATTRIBUTES_ATTR: entry_point.attr,
            self.KEY_ATTRIBUTES_EXTRAS: entry_point.extras,
            self.KEY_ATTRIBUTES_VERSION: VERSION_PROVIDER.get_version_info(loaded)['version'].get('plugin'),
        }
        self.base.attributes.set_many(attributes)

    def _validate(self) -> None:
        """Validate the entry point reference."""
        super()._validate()

        entry_point = EntryPoint(
            name=self.name,
            group=self.group,
            value=self.value,
        )

        try:
            self._validate_entry_point(entry_point)
        except (TypeError, ValueError) as exception:
            raise exceptions.ValidationError(str(exception)) from exception

        if self.module != entry_point.module:
            msg = f'Stored entry point module `{self.module}` does not match `{entry_point.module}`.'
            raise exceptions.ValidationError(msg)

        if self.attr != entry_point.attr:
            msg = f'Stored entry point attribute `{self.attr}` does not match `{entry_point.attr}`.'
            raise exceptions.ValidationError(msg)

        if self.extras != entry_point.extras:
            msg = f'Stored entry point extras `{self.extras}` do not match `{entry_point.extras}`.'
            raise exceptions.ValidationError(msg)

    @staticmethod
    def _validate_entry_point(entry_point: EntryPoint) -> t.Any:
        """Validate an entry point and return the loaded object."""
        try:
            loaded = entry_point.load()  # type: ignore[no-untyped-call]
        except ModuleNotFoundError as exception:
            msg = f'entry point `{entry_point}` could not be loaded.'
            raise ValueError(msg) from exception

        try:
            reloaded = get_entry_point(entry_point.group, entry_point.name).load()  # type: ignore[no-untyped-call]
        except EntryPointError as exception:
            msg = (
                f'Inconsistent entry point: the `name` and `group` of {entry_point} do not match any registered '
                'entry point.'
            )
            raise ValueError(msg) from exception

        if loaded != reloaded:
            msg = (
                f'Inconsistent entry point: the `name` and `group` of {entry_point} point to {reloaded} which does not '
                f'match the value `{entry_point.value}` of the specified entry point.'
            )
            raise ValueError(msg)

        return loaded

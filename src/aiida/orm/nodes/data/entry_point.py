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

from aiida.common import exceptions
from aiida.common.exceptions import EntryPointError
from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.decorators.attributes import attribute
from aiida.orm.nodes.data.data import Data
from aiida.plugins.entry_point import get_entry_point
from aiida.plugins.utils import PluginVersionProvider

__all__ = ('EntryPointData',)

LOGGER = AIIDA_LOGGER.getChild('entry_point')
VERSION_PROVIDER = PluginVersionProvider()


class EntryPointData(Data):
    """Data plugin to store a reference to an entry point.

    To construct an EntryPointData instance, use the class methods :meth:`from_entry_point_object`
    or :meth:`from_entry_point_parameters`.
    """

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

    KEY_ATTRIBUTES_EXTRAS: str = 'ep_extras'
    """Attribute key that stores the ``extras`` attribute of the wrapped entry point."""

    KEY_ATTRIBUTES_VERSION: str = 'version'
    """Attribute key that stores the version of the package that provided the entry point, if available."""

    def __init__(
        self,
        entry_point: EntryPoint | None = None,
        *,
        name: str | None = None,
        group: str | None = None,
        value: str | None = None,
        module: str | None = None,
        attr: str | None = None,
        ep_extras: list[str] | None = None,
        version: str | None = None,
        **kwargs: t.Any,
    ) -> None:
        """Construct a node representing a registered entry point.

        The entry point can be provided directly, identified by its group and
        name, or reconstructed from its stored attributes.
        """
        super().__init__(**kwargs)

        if entry_point is not None:
            type_check(entry_point, EntryPoint)
        elif name is not None and group is not None:
            if value is not None:
                entry_point = EntryPoint(name=name, group=group, value=value)
            else:
                try:
                    entry_point = get_entry_point(group, name)
                except EntryPointError as exception:
                    msg = f'entry point with group `{group}` and name `{name}` does not exist.'
                    raise ValueError(msg) from exception
        else:
            raise ValueError('Define either the `entry_point` directly or the `group` and `name`.')

        loaded = self._validate_entry_point(entry_point)

        provided = {
            'name': name,
            'group': group,
            'value': value,
            'module': module,
            'attr': attr,
            'ep_extras': ep_extras,
        }

        for key, supplied in provided.items():
            if supplied is None:
                continue

            actual = entry_point.extras if key == 'ep_extras' else getattr(entry_point, key)

            if supplied != actual:
                msg = f'Inconsistent entry point: supplied `{key}` is {supplied!r}, expected {actual!r}.'
                raise ValueError(msg)

        self._set_entry_point(entry_point, loaded, version=version)

    @attribute
    def name(self) -> str:
        """The name of the wrapped entry point."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_NAME)

    @name.setter
    def name(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_NAME, value)

    @attribute
    def group(self) -> str:
        """The group of the wrapped entry point."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_GROUP)

    @group.setter
    def group(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_GROUP, value)

    @attribute(required_once_stored=True)
    def value(self) -> str | None:
        """The value of the wrapped entry point."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_VALUE)

    @value.setter
    def value(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_VALUE, value)

    @attribute(required_once_stored=True)
    def module(self) -> str | None:
        """The module of the wrapped entry point."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_MODULE)

    @module.setter
    def module(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_MODULE, value)

    @attribute(required_once_stored=True)
    def attr(self) -> str | None:
        """The attribute of the wrapped entry point."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_ATTR)

    @attr.setter
    def attr(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_ATTR, value)

    @attribute(required_once_stored=True)
    def ep_extras(self) -> list[str] | None:
        """The extras of the wrapped entry point."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_EXTRAS)

    @ep_extras.setter
    def ep_extras(self, value: list[str]) -> None:
        type_check(value, list)
        self.base.attributes.set(self.KEY_ATTRIBUTES_EXTRAS, value)

    @attribute(required_once_stored=True)
    def version(self) -> str | None:
        """The version of the package that provided the entry point, if available."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_VERSION)

    @version.setter
    def version(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_VERSION, value)

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

    def _set_entry_point(
        self,
        entry_point: EntryPoint,
        loaded: t.Any,
        *,
        version: str | None = None,
    ) -> None:
        """Set the attributes describing an entry point."""
        if version is None:
            version = VERSION_PROVIDER.get_version_info(loaded)['version'].get('plugin')

        attributes = {
            self.KEY_ATTRIBUTES_NAME: entry_point.name,
            self.KEY_ATTRIBUTES_GROUP: entry_point.group,
            self.KEY_ATTRIBUTES_VALUE: entry_point.value,
            self.KEY_ATTRIBUTES_MODULE: entry_point.module,
            self.KEY_ATTRIBUTES_ATTR: entry_point.attr,
            self.KEY_ATTRIBUTES_EXTRAS: entry_point.extras,
            self.KEY_ATTRIBUTES_VERSION: version,
        }

        self.base.attributes.set_many(attributes)

    def _validate(self) -> None:
        super()._validate()

        try:
            self.name
            self.group
            self.value
        except AttributeError as exc:
            msg = f'missing `name`, `group`, or `value` attribute;\n\n{self.__doc__}'
            raise exceptions.ValidationError(msg) from exc

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

        if self.ep_extras != entry_point.extras:
            msg = f'Stored entry point extras `{self.ep_extras}` do not match `{entry_point.extras}`.'
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

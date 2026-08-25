###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for custom click param type identifier"""

from __future__ import annotations

import typing as t
from abc import ABC, abstractmethod
from functools import cached_property

import click

from aiida.plugins.entry_point import get_entry_point_from_string

if t.TYPE_CHECKING:
    from importlib_metadata import EntryPoint

    from aiida.orm.utils.loaders import OrmEntityLoader

__all__ = ('IdentifierParamType',)


class IdentifierParamType(click.ParamType, ABC):
    """An extension of click.ParamType for a generic identifier parameter. In AiiDA, orm entities can often be
    identified by either their ID, UUID or optionally some LABEL identifier. This parameter type implements
    the convert method, which attempts to convert a value passed to the command for a parameter with this type,
    to an orm entity. The actual loading of the entity is delegated to the orm class loader. Subclasses of this
    parameter type should implement the `orm_class_loader` method to return the appropriate orm class loader,
    which should be a subclass of `aiida.orm.utils.loaders.OrmEntityLoader` for the corresponding orm class.
    """

    def __init__(self, sub_classes: tuple[str, ...] | None = None):
        """Construct the parameter type, optionally specifying a tuple of entry points that reference classes
        that should be a sub class of the base orm class of the orm class loader. The classes pointed to by
        these entry points will be passed to the OrmEntityLoader when converting an identifier and they will
        restrict the query set by demanding that the class of the corresponding entity matches these sub classes.

        To prevent having to load the database environment at import time, the actual loading of the entry points
        is deferred until the call to `convert` is made. This is to keep the command line autocompletion light
        and responsive. The validation of entry point strings is also postponed for the same reason.

        :param sub_classes: a tuple of entry point strings that can narrow the set of orm classes that values
            will be mapped upon. These classes have to be strict sub classes of the base orm class defined
            by the orm class loader
        """
        if sub_classes is not None and not isinstance(sub_classes, tuple):
            raise TypeError('sub_classes should be a tuple of entry point strings')

        self._sub_classes: tuple[t.Any, ...] | None = None
        self._entry_point_strings = sub_classes

    @cached_property
    def _entry_points(self) -> list[EntryPoint]:
        """Allowed entry points, loaded on demand"""
        from aiida.common import exceptions

        if self._entry_point_strings is None:
            return []

        entry_points = []
        for entry_point_string in self._entry_point_strings:
            try:
                entry_point = get_entry_point_from_string(entry_point_string)
            except (ValueError, exceptions.EntryPointError) as exception:
                raise ValueError(f'{entry_point_string} is not a valid entry point string: {exception}')
            else:
                entry_points.append(entry_point)
        return entry_points

    @property
    @abstractmethod
    def orm_class_loader(self) -> OrmEntityLoader:
        """Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """

    @property
    def sub_classes(self) -> tuple[t.Any, ...] | None:
        """Return the orm classes that an identifier for this parameter is allowed to map onto.

        The entry points given to the constructor are resolved on first access. Resolving them only imports the classes
        they point to, so this does not require a storage backend.

        :return: the allowed sub classes, or ``None`` if the parameter does not restrict them.
        :raises RuntimeError: if an entry point cannot be loaded or does not point to a valid sub class.
        """
        if self._sub_classes is None and self._entry_points:
            loader = self.orm_class_loader
            sub_classes = []

            for entry_point in self._entry_points:
                try:
                    sub_class = entry_point.load()  # type: ignore[no-untyped-call]
                except ImportError as exception:
                    raise RuntimeError(f'failed to load the entry point {entry_point}: {exception}')

                if not issubclass(sub_class, loader.orm_base_class):
                    raise RuntimeError(
                        f'the class {sub_class} of entry point {entry_point} '
                        f'is not a sub class of {loader.orm_base_class}'
                    )
                else:
                    sub_classes.append(sub_class)

            self._sub_classes = tuple(sub_classes)

        return self._sub_classes

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        """Validate the identifier and return it unchanged.

        Resolving the identifier into an orm entity requires a storage backend, which parsing a command line must not
        need. Commands therefore resolve the identifier in their body through
        :mod:`aiida.cmdline.utils.loaders`, which calls :meth:`resolve`.

        :return: the identifier
        :raises click.BadParameter: if the value is empty
        """
        value = super().convert(value, param, ctx)

        if not value:
            raise click.BadParameter('the value for the identifier cannot be empty', ctx=ctx, param=param)

        return t.cast(str, value)

    def resolve(self, identifier: str) -> t.Any:
        """Return the orm entity that the identifier maps onto.

        Requires a loaded storage backend. Subclasses override this to apply checks that need the loaded entity.

        :param identifier: PK, UUID or label of the entity.
        :raises aiida.common.NotExistent: if the identifier maps onto no entity.
        :raises aiida.common.MultipleObjectsError: if the identifier is ambiguous.
        :raises RuntimeError: if the defined orm class loader is not a subclass of the OrmEntityLoader class.
        """
        from aiida.orm.utils.loaders import OrmEntityLoader

        loader = self.orm_class_loader

        if not issubclass(loader, OrmEntityLoader):
            raise RuntimeError('the orm class loader should be a subclass of OrmEntityLoader')

        return loader.load_entity(identifier, sub_classes=self.sub_classes)

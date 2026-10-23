###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin to store (almost) any Python object by pickling it."""

from __future__ import annotations

import importlib.metadata
import io
import typing as t

import pydantic as pdt

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.singlefile import SinglefileData

__all__ = ('PickledData',)

LOGGER = AIIDA_LOGGER.getChild('pickled_data')

_UNSET = object()


class PickledData(SinglefileData):
    """Data plugin to store (almost) any Python object by pickling it."""

    KEY_ATTRIBUTES_UNPICKLER_MODULE: str = 'unpickler_module'
    """Attribute key that stores the module of the function that can unpickle this object."""

    KEY_ATTRIBUTES_UNPICKLER_NAME: str = 'unpickler_name'
    """Attribute key that stores the name of the function that can unpickle this object."""

    KEY_ATTRIBUTES_UNPICKLER_VERSION: str = 'pickler_version'
    """Attribute key that stores the version of the package whose function can unpickle this object."""

    KEY_ATTRIBUTES_PICKLER_KWARGS: str = 'pickler_kwargs'
    """Attribute key that stores the keyword arguments passed to the constructor which are forwarded to the pickler."""

    # TODO tighten this!
    def __init__(
        self,
        obj: t.Any | None = _UNSET,
        *,
        unpickler_module: str | None = None,
        unpickler_name: str | None = None,
        pickler_version: str | None = None,
        pickler_kwargs: dict[str, t.Any] | None = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)

        if obj is not _UNSET:
            pickler_kwargs = pickler_kwargs or {}
            pickled = self._get_pickler()(obj, **pickler_kwargs)
            self.set_file(io.BytesIO(pickled))
            self._set_unpickler_information()
            self.pickler_kwargs = pickler_kwargs
        elif unpickler_module is not None and unpickler_name is not None:
            self._set_unpickler_attributes(
                unpickler_module=unpickler_module,
                unpickler_name=unpickler_name,
                pickler_version=pickler_version,
            )

    @attribute
    def unpickler_module(self) -> str:
        """The module of the function that can unpickle this object."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_UNPICKLER_MODULE)

    @unpickler_module.setter
    def unpickler_module(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_UNPICKLER_MODULE, value)

    @attribute
    def unpickler_name(self) -> str:
        """The name of the function that can unpickle this object."""
        return self.base.attributes.get(self.KEY_ATTRIBUTES_UNPICKLER_NAME)

    @unpickler_name.setter
    def unpickler_name(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_UNPICKLER_NAME, value)

    @attribute
    def pickler_version(self) -> str | None:
        """The version of the package whose function can unpickle this object."""
        return t.cast(str | None, self.base.attributes.get(self.KEY_ATTRIBUTES_UNPICKLER_VERSION))

    @pickler_version.setter
    def pickler_version(self, value: str | None) -> None:
        if value is not None:
            type_check(value, str)
        self.base.attributes.set(self.KEY_ATTRIBUTES_UNPICKLER_VERSION, value)

    @attribute(model_field_info=pdt.fields.FieldInfo(default_factory=dict))
    def pickler_kwargs(self) -> dict[str, t.Any]:
        """The keyword arguments forwarded to the pickler."""
        return t.cast(dict[str, t.Any], self.base.attributes.get(self.KEY_ATTRIBUTES_PICKLER_KWARGS))

    @pickler_kwargs.setter
    def pickler_kwargs(self, value: dict[str, t.Any]) -> None:
        type_check(value, dict)
        self.base.attributes.set(self.KEY_ATTRIBUTES_PICKLER_KWARGS, value)

    def get_unpickler_information(self) -> tuple[str, str, str | None]:
        """Return tuple of module name, function name and version of the package that can unpickle this object."""
        return self.unpickler_module, self.unpickler_name, self.pickler_version

    def get_unpickler(self) -> t.Callable[[bytes], t.Any]:
        """Return the method to be used for unpickling the object.

        :returns: A callable that takes a number of bytes and unpickles it into the original Python object.
        :raises RuntimeError: If the required unpickling method could not be loaded.
        """
        module, name, pickled_version = self.get_unpickler_information()
        package = module.split('.', maxsplit=1)[0]

        requirement = f'{package}=={pickled_version}' if pickled_version is not None else package

        try:
            unpickler_module = importlib.import_module(module)
        except ImportError as exception:
            msg = (
                f'Could not import module `{module}` which should be able to unpickle this node. '
                f'Install `{requirement}` and try again.'
            )
            raise RuntimeError(msg) from exception

        try:
            unpickler: t.Callable[[bytes], t.Any] = getattr(unpickler_module, name)
        except AttributeError as exception:
            msg = (
                f'Could not load `{name}` from `{module}` which should be able to unpickle this node. '
                f'Install `{requirement}` and try again.'
            )
            raise RuntimeError(msg) from exception

        try:
            installed_version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            installed_version = None

        if installed_version != pickled_version:
            LOGGER.warning(
                f'This node was pickled with `{package}=={pickled_version}` but version `{installed_version}` is '
                'installed. It is possible that the unpickling may fail.'
            )

        return unpickler

    def load(self) -> t.Any:
        """Load the pickled Python object.

        :returns: The unpickled Python object.
        :raises ValueError: If the stored pickled object could not be unpickled.
        """
        with self.open(mode='rb') as handle:
            pickled = handle.read()

        try:
            unpickled = self.get_unpickler()(pickled)
        except Exception as exception:
            msg = 'The pickled object could not be unpickled.'
            raise ValueError(msg) from exception

        return unpickled

    @classmethod
    def _get_pickler(cls) -> t.Callable[..., bytes]:
        """Return the function that should be used to pickle the object stored by this node.

        Subclasses override this, and :meth:`_get_default_unpickler`, to store objects with a different pickler.

        :returns: A callable that is used to pickle the object to be stored by this node.
        """
        import dill

        pickler: t.Callable[..., bytes] = dill.dumps
        return pickler

    @classmethod
    def _get_default_unpickler(cls) -> t.Callable[[bytes], t.Any]:
        """Return the function that this class records as being able to unpickle the objects it stores.

        This is the counterpart of :meth:`_get_pickler`. It is not :meth:`get_unpickler`, which returns the
        function that a given node recorded when it was created.

        :returns: A callable that takes a number of bytes and unpickles it into the original Python object.
        """
        import dill

        unpickler: t.Callable[[bytes], t.Any] = dill.loads
        return unpickler

    def _set_unpickler_information(self) -> None:
        """Store the module, function and version of the package that can be used for unpickling this object.

        .. note:: If the version of the package cannot be determined, it will be set to ``None``.
        """
        unpickler = self._get_default_unpickler()
        package = unpickler.__module__.split('.', maxsplit=1)[0]

        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = None

        self._set_unpickler_attributes(
            unpickler_module=unpickler.__module__,
            unpickler_name=unpickler.__name__,
            pickler_version=version,
        )

    def _set_unpickler_attributes(
        self,
        unpickler_module: str,
        unpickler_name: str,
        pickler_version: str | None,
    ) -> None:
        """Set the unpickler attributes for this node."""
        self.base.attributes.set_many(
            {
                self.KEY_ATTRIBUTES_UNPICKLER_MODULE: unpickler_module,
                self.KEY_ATTRIBUTES_UNPICKLER_NAME: unpickler_name,
                self.KEY_ATTRIBUTES_UNPICKLER_VERSION: pickler_version,
            }
        )

    def _validate(self) -> None:
        super()._validate()

        try:
            self.unpickler_module
            self.unpickler_name
        except AttributeError as exception:
            raise exceptions.ValidationError('missing unpickler information') from exception

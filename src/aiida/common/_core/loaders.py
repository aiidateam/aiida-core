###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Load Python objects from persistent identifiers."""

from __future__ import annotations

import abc
import importlib
import inspect
import types
from collections import deque
from typing import Any


class ObjectLoader(abc.ABC):
    """Interface for identifying and loading Python objects."""

    @abc.abstractmethod
    def load_object(self, identifier: str) -> Any:
        """Load the object represented by an identifier."""

    @abc.abstractmethod
    def identify_object(self, obj: Any) -> str:
        """Return the persistent identifier for an object."""


class DefaultObjectLoader(ObjectLoader):
    """Load module-level classes, functions, and constants."""

    def load_object(self, identifier: str) -> Any:
        """Load an object identified as ``module:name``."""
        try:
            module_name, name = identifier.split(':')
        except ValueError as exception:
            msg = f'identifier `{identifier}` has an invalid format.'
            raise ImportError(msg) from exception

        try:
            module = importlib.import_module(module_name)
        except ImportError as exception:
            msg = f"module '{module_name}' from identifier '{identifier}' could not be loaded"
            raise ImportError(msg) from exception

        try:
            return getattr(module, name)
        except AttributeError as exception:
            msg = f"object '{name}' from identifier '{identifier}' could not be loaded"
            raise ImportError(msg) from exception

    def identify_object(self, obj: Any) -> str:
        """Return an importable identifier for an object."""
        identifier = f'{obj.__module__}:{obj.__name__}'
        self.load_object(identifier)
        return identifier


OBJECT_LOADER: ObjectLoader | None = None


def get_object_loader() -> ObjectLoader:
    """Return the global object loader."""
    global OBJECT_LOADER  # noqa: PLW0603
    if OBJECT_LOADER is None:
        OBJECT_LOADER = DefaultObjectLoader()
    return OBJECT_LOADER


def load_function(name: str, instance: Any | None = None) -> Any:
    """Load a function from its fully qualified name."""
    obj = load_object(name)
    if inspect.ismethod(obj) and instance is not None:
        return obj.__get__(instance, instance.__class__)  # type: ignore[attr-defined]
    if inspect.ismethod(obj) or inspect.isfunction(obj):
        return obj
    raise ValueError(f"Invalid function name '{name}'")


def load_object(fullname: str) -> Any:
    """Load an object from a fully qualified name."""
    obj, remainder = load_module(fullname)
    for name in remainder:
        try:
            obj = getattr(obj, name)
        except AttributeError as exception:
            raise ValueError(f"Could not load object corresponding to '{fullname}'") from exception
    return obj


def load_module(fullname: str) -> tuple[types.ModuleType, deque[str]]:
    """Load the longest importable module prefix from a fully qualified name."""
    parts = fullname.split('.')
    remainder: deque[str] = deque()
    for _ in range(len(parts)):
        try:
            return importlib.import_module('.'.join(parts)), remainder
        except ImportError:
            remainder.appendleft(parts.pop())
    raise ValueError(f"Could not load a module corresponding to '{fullname}'")

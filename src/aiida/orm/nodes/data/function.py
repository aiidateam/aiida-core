###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a reference to a Python function or class."""

from __future__ import annotations

import types
from importlib import import_module

from .base import to_aiida_type
from .data import Data

__all__ = ('FunctionData',)


@to_aiida_type.register(types.FunctionType)
def _(value):
    return FunctionData(value)


class FunctionData(Data):
    """`Data` sub class that stores an importable reference to a Python function or class.

    Only the module path and qualified name are stored, so the referenced object must be importable in the environment
    that later resolves it through :attr:`value`; the object itself is not serialized.
    """

    def __init__(self, value, **kwargs):
        module = getattr(value, '__module__', None)
        qualname = getattr(value, '__qualname__', None) or getattr(value, '__name__', None)
        if not module or not qualname:
            msg = f'expected a function-like object with a module and qualified name, got {type(value)}'
            raise TypeError(msg)
        super().__init__(**kwargs)
        self.base.attributes.set('module_path', module)
        self.base.attributes.set('qualname', qualname)

    @property
    def module_path(self) -> str:
        return self.base.attributes.get('module_path')

    @property
    def qualname(self) -> str:
        return self.base.attributes.get('qualname')

    @property
    def path(self) -> str:
        return f'{self.module_path}:{self.qualname}'

    @property
    def value(self):
        """Import and return the referenced function or class.

        :raises ImportError: if the module cannot be imported or the qualified name cannot be resolved within it.
        """
        try:
            module = import_module(self.module_path)
        except Exception as exc:
            msg = f"failed to import module '{self.module_path}' for FunctionData '{self.path}': {exc}"
            raise ImportError(msg) from exc

        obj = module
        try:
            for part in self.qualname.split('.'):
                obj = getattr(obj, part)
        except AttributeError as exc:
            msg = f"failed to resolve '{self.path}': attribute '{part}' not found."
            raise ImportError(msg) from exc

        return obj

    def __str__(self) -> str:
        return self.path

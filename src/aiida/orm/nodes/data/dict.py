###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a dictionary."""

from __future__ import annotations

import typing as t
from collections.abc import Mapping, MutableMapping
from copy import deepcopy

import pydantic as pdt

from aiida.common.lang import override
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.orm.nodes.data.data import Data, DataInterface

if t.TYPE_CHECKING:
    from aiida.orm.utils.managers import AttributeManager

__all__ = ('Dict', 'DictInterface')


class Dict(Data):
    """A data node that stores each dictionary entry as a node attribute."""

    _attributes_model_config = pdt.ConfigDict(extra='allow')
    _cli_expose_extra_attributes = True

    @property
    def dict(self) -> AttributeManager:
        """Return an `AttributeManager` wrapper of this node.

        This allows `node.dict.key` and `node.dict[key]`.
        """
        from aiida.orm.utils.managers import AttributeManager

        return AttributeManager(self)


class DictInterface(DataInterface[Dict], MutableMapping[str, t.Any]):
    """An in-memory mapping interface for the `Dict` data type."""

    _orm_cls = Dict

    def __init__(self, value: Mapping[str, t.Any] | None = None) -> None:
        """Initialize the interface with a copy of a mapping."""
        self.value = deepcopy(dict(value)) if value is not None else {}

    def __getitem__(self, key: str) -> t.Any:
        return self.value[key]

    def __setitem__(self, key: str, value: t.Any) -> None:
        self.value[key] = value

    def __delitem__(self, key: str) -> None:
        del self.value[key]

    def __iter__(self) -> t.Iterator[str]:
        return iter(self.value)

    def __len__(self) -> int:
        return len(self.value)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.value!r})'

    @override
    def _get_attributes(self) -> dict[str, t.Any]:
        """Return a dictionary of the attributes for this interface."""
        return deepcopy(self.value)

    @override
    def _set_attributes(self, entity: Dict) -> None:
        """Set the attributes for this interface from the given entity."""
        self.value = deepcopy(entity.attributes)


@to_aiida_type.register(dict)
def _(value: dict[str, t.Any]) -> Dict:
    return Dict(attributes=deepcopy(value))

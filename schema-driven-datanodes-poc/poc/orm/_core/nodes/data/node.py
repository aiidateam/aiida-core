###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Core data-node object for the PoC."""

from __future__ import annotations

import typing as t

from poc.orm._core.nodes.node import Node


class Data(Node):
    """Core data-node state: a node plus a schema name and stored values."""

    schema_name: t.ClassVar[str] = 'Data'

    def __init__(self, **values: t.Any) -> None:
        label = t.cast('str', values.pop('label', ''))
        uuid = t.cast('str', values.pop('uuid', ''))
        super().__init__(uuid=uuid, label=label)
        self.values = values

    @classmethod
    def from_values(cls, values: dict[str, t.Any]) -> t.Self:
        """Construct a data node from payload values already validated elsewhere."""
        return cls(**values)

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}(schema_name={self.schema_name!r}, uuid={self.uuid!r}, '
            f'label={self.label!r}, values={self.values!r})'
        )

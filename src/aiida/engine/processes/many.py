###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Annotations for keyed collections of process ports."""

import typing as t

_ManyType = t.TypeVar('_ManyType')


class Many(dict[str, _ManyType]):
    """Annotates a keyed collection whose names are known only at runtime.

    Task inputs receive a mapping. Fields in a task's output ``PortModel``
    declare dynamic namespaces, with each value stored as a separate node.
    Ordinary dictionary annotations instead declare one dictionary value port.
    """


def _takes_many(annotation: t.Any) -> bool:
    """Return whether an annotation declares a keyed collection of ports."""
    return annotation is Many or t.get_origin(annotation) is Many

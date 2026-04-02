###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapter module for optional aiida-workgraph integration.

Provides a helper for detecting WorkGraph instances so that
``aiida.engine.run`` / ``submit`` can dispatch to the WorkGraph launch path.
"""

# mypy: disable-error-code="unused-ignore"
# aiida-workgraph is an optional dependency: mypy raises import-not-found when
# it is absent and import-untyped when it is present.  Both codes are needed in
# type-ignore comments, but one will always be unused, so we suppress that check.
from __future__ import annotations

import typing as t

try:
    import aiida_workgraph  # type: ignore[import-not-found,import-untyped]  # noqa: F401

    WORKGRAPH_AVAILABLE = True
except ImportError:
    WORKGRAPH_AVAILABLE = False


def is_workgraph_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraph instance.

    Returns False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraph instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph import WorkGraph  # type: ignore[import-not-found,import-untyped]

    return isinstance(obj, WorkGraph)

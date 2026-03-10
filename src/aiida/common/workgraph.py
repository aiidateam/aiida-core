###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapter module for optional aiida-workgraph integration.

This module provides a centralized location for checking availability
of aiida-workgraph components. It allows aiida-core to optionally support WorkGraph
processes without requiring aiida-workgraph as a dependency.

Usage:
    from aiida.common.workgraph import WORKGRAPH_AVAILABLE, is_workgraph_instance

    if is_workgraph_instance(process):
        # WorkGraph-specific code
        ...
"""

from __future__ import annotations

import typing as t

# Check if aiida-workgraph is available
try:
    import aiida_workgraph  # type: ignore[import-not-found]  # noqa: F401

    WORKGRAPH_AVAILABLE = True
except ImportError:
    WORKGRAPH_AVAILABLE = False


def is_workgraph_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraph instance.

    This helper function safely checks if an object is a WorkGraph instance,
    returning False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraph instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph import WorkGraph

    return isinstance(obj, WorkGraph)


def is_workgraph_node_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraphNode instance.

    This helper function safely checks if an object is a WorkGraphNode instance,
    returning False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraphNode instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph.orm.workgraph import WorkGraphNode  # type: ignore[import-not-found]

    return isinstance(obj, WorkGraphNode)

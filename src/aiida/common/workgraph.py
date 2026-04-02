###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapter module for optional ``aiida-workgraph`` integration.

``aiida-workgraph`` is an **optional** dependency. This module centralises the
availability check and type detection so that other modules (e.g.
``aiida.engine.launch``) do not need to handle optional-dependency imports
themselves.

Type checkers will report missing-import warnings here; these are expected
and unavoidable for this optional-dependency pattern.
"""

# mypy: disable-error-code="unused-ignore"
# mypy raises import-not-found when aiida-workgraph is absent and
# import-untyped when it is present. Both codes are needed in type-ignore
# comments, but one will always be unused, so we suppress that check.
from __future__ import annotations

import typing as t

try:
    import aiida_workgraph  # type: ignore[import-not-found,import-untyped]  # noqa: F401

    WORKGRAPH_INSTALLED = True
except ImportError:
    WORKGRAPH_INSTALLED = False


def is_workgraph_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraph instance.

    This helper exists so that call sites (e.g. ``aiida.engine.launch``) do not
    need ``from aiida_workgraph import WorkGraph`` and the associated
    ``try/except ImportError`` boilerplate. The import is confined to this module
    instead.

    Guard with ``WORKGRAPH_INSTALLED`` first to separate the availability
    question from the type question.

    :param obj: The object to check.
    :return: True if obj is a WorkGraph instance.
    :raises ImportError: if aiida-workgraph is not installed.
    """
    from aiida_workgraph import WorkGraph  # type: ignore[import-not-found,import-untyped]

    return isinstance(obj, WorkGraph)

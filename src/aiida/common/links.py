###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with utilities and data structures pertaining to links between nodes in the provenance graph."""

from collections import namedtuple
from enum import Enum

from .lang import isidentifier, type_check

__all__ = ('GraphTraversalRule', 'GraphTraversalRules', 'LinkType', 'validate_link_label')


class LinkType(Enum):
    """A simple enum of allowed link types."""

    CREATE = 'create'
    RETURN = 'return'
    INPUT_CALC = 'input_calc'
    INPUT_WORK = 'input_work'
    CALL_CALC = 'call_calc'
    CALL_WORK = 'call_work'


GraphTraversalRule = namedtuple('GraphTraversalRule', ['link_type', 'direction', 'toggleable', 'default'])
"""A namedtuple that defines a graph traversal rule.

When starting from a certain sub set of nodes, the graph traversal rules specify which links should be followed to
add adjacent nodes to finally arrive at a set of nodes that represent a valid and consistent sub graph.

:param link_type: the `LinkType` that the rule applies to
:param direction: whether the link type should be followed backwards or forwards
:param toggleable: boolean to indicate whether the rule can be changed from the default value. If this is `False` it
    means the default value can never be changed as it will result in an inconsistent graph.
:param default: boolean, the default value of the rule, if `True` means that the link type for the given direction
    should be followed.
"""


class GraphTraversalRules(Enum):
    """Graph traversal rules when deleting or exporting nodes."""

    DEFAULT = {
        'input_calc_forward': GraphTraversalRule(LinkType.INPUT_CALC, 'forward', True, False),
        'input_calc_backward': GraphTraversalRule(LinkType.INPUT_CALC, 'backward', True, False),
        'create_forward': GraphTraversalRule(LinkType.CREATE, 'forward', True, False),
        'create_backward': GraphTraversalRule(LinkType.CREATE, 'backward', True, False),
        'return_forward': GraphTraversalRule(LinkType.RETURN, 'forward', True, False),
        'return_backward': GraphTraversalRule(LinkType.RETURN, 'backward', True, False),
        'input_work_forward': GraphTraversalRule(LinkType.INPUT_WORK, 'forward', True, False),
        'input_work_backward': GraphTraversalRule(LinkType.INPUT_WORK, 'backward', True, False),
        'call_calc_forward': GraphTraversalRule(LinkType.CALL_CALC, 'forward', True, False),
        'call_calc_backward': GraphTraversalRule(LinkType.CALL_CALC, 'backward', True, False),
        'call_work_forward': GraphTraversalRule(LinkType.CALL_WORK, 'forward', True, False),
        'call_work_backward': GraphTraversalRule(LinkType.CALL_WORK, 'backward', True, False),
    }

    DELETE = {
        'input_calc_forward': GraphTraversalRule(LinkType.INPUT_CALC, 'forward', False, True),
        'input_calc_backward': GraphTraversalRule(LinkType.INPUT_CALC, 'backward', False, False),
        'create_forward': GraphTraversalRule(LinkType.CREATE, 'forward', True, True),
        'create_backward': GraphTraversalRule(LinkType.CREATE, 'backward', False, True),
        'return_forward': GraphTraversalRule(LinkType.RETURN, 'forward', False, False),
        'return_backward': GraphTraversalRule(LinkType.RETURN, 'backward', False, True),
        'input_work_forward': GraphTraversalRule(LinkType.INPUT_WORK, 'forward', False, True),
        'input_work_backward': GraphTraversalRule(LinkType.INPUT_WORK, 'backward', False, False),
        'call_calc_forward': GraphTraversalRule(LinkType.CALL_CALC, 'forward', True, True),
        'call_calc_backward': GraphTraversalRule(LinkType.CALL_CALC, 'backward', False, True),
        'call_work_forward': GraphTraversalRule(LinkType.CALL_WORK, 'forward', True, True),
        'call_work_backward': GraphTraversalRule(LinkType.CALL_WORK, 'backward', False, True),
    }

    EXPORT = {
        'input_calc_forward': GraphTraversalRule(LinkType.INPUT_CALC, 'forward', True, False),
        'input_calc_backward': GraphTraversalRule(LinkType.INPUT_CALC, 'backward', False, True),
        'create_forward': GraphTraversalRule(LinkType.CREATE, 'forward', False, True),
        'create_backward': GraphTraversalRule(LinkType.CREATE, 'backward', True, True),
        'return_forward': GraphTraversalRule(LinkType.RETURN, 'forward', False, True),
        'return_backward': GraphTraversalRule(LinkType.RETURN, 'backward', True, False),
        'input_work_forward': GraphTraversalRule(LinkType.INPUT_WORK, 'forward', True, False),
        'input_work_backward': GraphTraversalRule(LinkType.INPUT_WORK, 'backward', False, True),
        'call_calc_forward': GraphTraversalRule(LinkType.CALL_CALC, 'forward', False, True),
        'call_calc_backward': GraphTraversalRule(LinkType.CALL_CALC, 'backward', True, True),
        'call_work_forward': GraphTraversalRule(LinkType.CALL_WORK, 'forward', False, True),
        'call_work_backward': GraphTraversalRule(LinkType.CALL_WORK, 'backward', True, True),
    }


def validate_link_label(link_label: str) -> None:
    """Validate the given link label.

    Valid link labels adhere to the following restrictions:

        * Has to be a valid python identifier
        * Can only contain alphanumeric characters and underscores
        * Can not start or end with an underscore

    :raises TypeError: if the link label is not a string type
    :raises ValueError: if the link label is invalid
    """
    import re

    message = f'invalid link label `{link_label}`: should be string type but is instead: {type(link_label)}'
    type_check(link_label, str, message)

    allowed_character_set = '[a-zA-Z0-9_]'

    if link_label.endswith('_'):
        raise ValueError('cannot end with an underscore')

    if link_label.startswith('_'):
        raise ValueError('cannot start with an underscore')

    if re.sub(allowed_character_set, '', link_label):
        raise ValueError('only alphanumeric and underscores are allowed')

    if not isidentifier(link_label):
        raise ValueError('not a valid python identifier')

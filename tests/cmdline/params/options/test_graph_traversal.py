###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for graph traversal command-line options."""

from aiida.cmdline.params.options.main import TRAVERSAL_RULE_HELP_STRING
from aiida.common.links import GraphTraversalRules


def test_graph_traversal_rule_help_strings_exhaustive():
    """Test all toggleable traversal rules have a CLI help string."""
    missing = {
        name
        for ruleset in GraphTraversalRules
        for name, rule in ruleset.value.items()
        if rule.toggleable and name not in TRAVERSAL_RULE_HELP_STRING
    }

    assert not missing

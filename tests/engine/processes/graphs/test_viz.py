###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################

import pytest

from aiida.engine.processes.graphs.viz import _label, _node_id, to_mermaid
from tests.engine.processes.graphs.programs import branches, calls, loops, ports

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    ('declaration', 'present', 'absent'),
    [
        pytest.param(
            calls.diamond.build(),
            [
                'flowchart TD',
                'in__x{{x}}',
                'in__x -->|x| add',
                'in__x -->|x| add_2',
                'add -->|result -> x| add_3',
                'add_2 -->|result -> y| add_3',
                'add_3 -->|result| out__result',
            ],
            [],
            id='diamond',
        ),
        pytest.param(
            calls.nested_multiply_add.build(),
            [
                'multiply_add["multiply_add"]',
                'multiply_add__multiply["multiply_add/multiply"]',
                'multiply_add --> multiply_add__in__x',
                'multiply_add -->|result -> x| add',
            ],
            ['-.->', 'multiply_add__in__x{{x}}\n    multiply_add__in__x{{x}}'],
            id='nested',
        ),
        pytest.param(
            branches.external_choice.build(),
            [
                'branch_1["branch_1"]',
                'branch_1__add["branch_1/add"]',
                'branch_1__otherwise__add["branch_1/otherwise/add"]',
                'branch_1 --> branch_1__in__value',
                'branch_1__in__value -->|x| branch_1__add',
                'branch_1 --> branch_1__otherwise__in__value',
                'branch_1__otherwise__in__value -->|x| branch_1__otherwise__add',
                'branch_1 -->|result| out__result',
            ],
            ['-.->'],
            id='branch',
        ),
        pytest.param(
            loops.countdown.build(),
            [
                'loop_1["loop_1"]',
                'loop_1 --> loop_1__in__value',
                'loop_1 --> loop_1__in__condition',
                'loop_1__decrement -->|result -> value| loop_1__is_positive',
                'loop_1 -->|value| out__value',
            ],
            ['-.->', 'loop_1__in__value{{value}}\n    loop_1__in__value{{value}}'],
            id='loop',
        ),
        pytest.param(
            ports.nested_passthrough.build(),
            ['in__config{{config}}', 'in__config -->|config.settings.count| out__count'],
            ['in__config_settings_count'],
            id='passthrough',
        ),
        pytest.param(
            calls.ordered.build(),
            ['in__x -->|x| add', 'prepare --> add', 'add -->|result| out__result'],
            ['prepare -->|'],
            id='after',
        ),
    ],
)
def test_renders_wirings(declaration, present: list[str], absent: list[str]) -> None:
    """Graphs render wirings and inputs as Mermaid flowcharts."""
    chart = to_mermaid(declaration)
    assert chart.startswith('flowchart TD\n')
    for fragment in present:
        assert fragment in chart
    for fragment in absent:
        assert fragment not in chart


def test_label_neutralizes_hostile_characters() -> None:
    """Quotes, pipes, and backslashes cannot break the Mermaid label syntax."""
    assert _label('say "hi" | now\\soon') == "say 'hi' / now\\\\soon"


def test_node_id_sanitizes_hostile_names() -> None:
    """Placement names with punctuation collapse to safe Mermaid identifiers."""
    assert _node_id('a b', 'c.d-e') == 'a_b__c_d_e'

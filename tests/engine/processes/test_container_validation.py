###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for what a container says about the namespace its fields name."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field, field_validator

from aiida.engine import graph, run_get_node, task


class PhInputs(BaseModel):
    structure: str
    ecutwfc: float = Field(default=60.0, le=200)

    @field_validator('structure')
    @classmethod
    def _named(cls, value):
        if not value:
            raise ValueError('a structure has to be named')
        return value


@task(outputs=['dielectric'])
def ph(given: PhInputs) -> float:
    return given.ecutwfc / 10.0


def test_the_container_takes_what_it_says_it_does():
    """The namespace is the fields of the container, so what the container accepts is what runs."""
    results, node = run_get_node(ph, given={'structure': 'si', 'ecutwfc': 120.0})

    assert node.is_finished_ok, node.exit_message
    assert results['dielectric'].value == 12.0


@pytest.mark.parametrize(
    'given, says',
    (
        ({'structure': 'si', 'ecutwfc': 500.0}, 'less than or equal to 200'),
        ({'structure': '', 'ecutwfc': 60.0}, 'a structure has to be named'),
    ),
    ids=('constraint', 'validator'),
)
def test_what_the_container_refuses_is_refused_at_submit(given, says):
    """A `Field` constraint and a validator of the container's own both answer before anything is stored."""
    with pytest.raises(ValueError, match=says):
        run_get_node(ph, given=given)


@graph
def pipeline(structure):
    return {'dielectric': ph(given={'structure': structure, 'ecutwfc': 500.0}).dielectric}


def test_a_value_written_into_a_graph_is_refused_when_its_task_is_submitted():
    """A literal in a graph is checked where the task it feeds is submitted, which running one surfaces at once."""
    with pytest.raises(ValueError, match='less than or equal to 200'):
        run_get_node(pipeline, structure='si')

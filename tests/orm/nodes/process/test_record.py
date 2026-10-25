###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for what a process notes about what it did outside the database."""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.common.exceptions import ModificationNotAllowed


def test_a_process_records_nothing_to_begin_with():
    """There is nothing to read back until something has been done."""
    assert orm.CalcFunctionNode().record == {}


def test_what_is_noted_is_read_back():
    """The point of the record: a step writes down what it did, and finds it again."""
    node = orm.CalcFunctionNode().store()
    node.set_record(job_id='1234')

    assert orm.load_node(node.pk).record == {'job_id': '1234'}


def test_noting_something_keeps_what_was_noted_before():
    """A step accumulates, so the second note does not lose the first."""
    node = orm.CalcFunctionNode().store()
    node.set_record(job_id='1234')
    node.set_record(directory='/scratch/1234')

    assert node.record == {'job_id': '1234', 'directory': '/scratch/1234'}


def test_the_record_stops_when_the_process_does():
    """It is updatable while the process runs, which is the window in which it means anything."""
    node = orm.CalcFunctionNode().store()
    node.set_record(job_id='1234')
    node.seal()

    with pytest.raises(ModificationNotAllowed):
        node.set_record(job_id='5678')


def test_what_is_noted_does_not_change_what_a_process_caches_against():
    """Two runs that did the same thing are the same run, whatever each had to note along the way."""
    first = orm.CalcFunctionNode()
    first.base.attributes.set('what', 'the same')
    first.store()

    second = orm.CalcFunctionNode()
    second.base.attributes.set('what', 'the same')
    second.store()
    second.set_record(job_id='only on this one')

    assert first.base.caching.get_hash() == second.base.caching.get_hash()

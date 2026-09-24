###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.engine.processes.persistence`."""

import logging
import sys

import pytest

from aiida.engine.processes import persistence
from aiida.engine.processes.persistence import (
    META,
    META__CLASS_BYTES,
    META__CLASS_NAME,
    CheckpointSerializable,
)


def test_load_prefers_a_carried_class_over_the_name(
    user_serializable: type[CheckpointSerializable], unresolvable_in_main
):
    """Only a class no name reaches travels, which is what reporting ``__main__`` makes of this one."""
    saved = unresolvable_in_main(user_serializable)('carried').save()

    assert CheckpointSerializable._get_class_bytes(saved) is not None

    # The name is now unresolvable, so anything that comes back came out of the process class bytes.
    saved[META][META__CLASS_NAME] = 'no.such.module:Missing'

    assert CheckpointSerializable.load(saved).value == 'carried'


def test_load_falls_back_to_the_name_when_the_carried_class_will_not_load(
    user_serializable: type[CheckpointSerializable],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    unresolvable_in_main,
):
    """A checkpoint carrying a class may still fail to deserialize it, on nothing more than a difference in
    interpreter or ``cloudpickle`` version, and the name is what it falls back to.

    The class both reports ``__main__``, so that it travels, and is bound there, so that the name resolves in this
    interpreter, which is the submitting kernel's own view of a class defined in a cell.
    """
    carried = unresolvable_in_main(user_serializable)
    monkeypatch.setattr(sys.modules['__main__'], carried.__name__, carried, raising=False)
    out_state = carried(value='carried').save()

    assert out_state[META][META__CLASS_BYTES], 'the class was not carried, so there is no fallback to test'

    out_state[META][META__CLASS_BYTES] = b'not a pickle'

    with caplog.at_level(logging.WARNING, logger=persistence.LOGGER.name):
        loaded = CheckpointSerializable.load(out_state)

    assert isinstance(loaded, user_serializable)
    assert loaded.value == 'carried'
    assert 'recorded name is being followed instead' in caplog.text


def test_load_reports_the_carried_failure_when_the_name_is_gone_too():
    """A notebook class whose bytes will not load leaves a name that was never going to resolve, so the loader's own
    error blames ``__main__``. The bytes were the route that should have worked, so their failure is the cause worth
    reporting, along with the two situations that produce it.
    """
    from aiida.engine.processes.persistence import META, META__CLASS_BYTES, META__CLASS_NAME

    saved = {META: {META__CLASS_NAME: '__main__:NotebookClass', META__CLASS_BYTES: b'not a pickle at all'}}

    with pytest.raises(ImportError) as info:
        CheckpointSerializable.load(saved)

    message = str(info.value)

    assert 'could not be recovered' in message
    assert 'invalid load key' in message, 'the unpickling failure is the cause and has to be in the message'
    assert '__main__:NotebookClass' in message
    assert 'PYTHONPATH' in message, 'a module the worker cannot import is the likelier cause, so name its fix'
    assert 'verdi daemon restart' in message, 'and the fix for the other one'
    assert 'cloudpickle' in message, 'the other one'
    assert info.value.__cause__ is not None, 'the unpickling failure is the chained cause'

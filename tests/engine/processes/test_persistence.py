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

import pytest

from aiida.engine.processes import _class_identity, persistence
from aiida.engine.processes.persistence import (
    META,
    META__CLASS_BYTES,
    META__CLASS_NAME,
    CheckpointSerializable,
)


def test_load_prefers_a_carried_class_over_the_name(
    user_serializable: type[CheckpointSerializable], monkeypatch: pytest.MonkeyPatch, worker_without: tuple[str, ...]
):
    monkeypatch.setattr(_class_identity, 'get_daemon_import_paths', lambda: worker_without)
    saved = user_serializable('carried').save()

    assert CheckpointSerializable._get_class_bytes(saved) is not None

    # The name is now unresolvable, so anything that comes back came out of the process class bytes.
    saved[META][META__CLASS_NAME] = 'no.such.module:Missing'

    assert CheckpointSerializable.load(saved).value == 'carried'


def test_load_falls_back_to_the_name_when_the_carried_class_will_not_load(
    user_serializable: type[CheckpointSerializable],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    worker_without: tuple[str, ...],
):
    """A submitter whose daemon cannot import a class carries it, and a worker that can import it may still fail to
    deserialize it, on nothing more than a difference in interpreter or ``cloudpickle`` version.
    """
    monkeypatch.setattr(_class_identity, 'get_daemon_import_paths', lambda: worker_without)
    out_state = user_serializable(value='carried').save()

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

    Submitting against a daemon from another installation is not among them: that is refused at submit, so naming it
    here would send a reader after the one cause this cannot be.
    """
    from aiida.engine.processes.persistence import META, META__CLASS_BYTES, META__CLASS_NAME

    saved = {META: {META__CLASS_NAME: '__main__:NotebookClass', META__CLASS_BYTES: b'not a pickle at all'}}

    with pytest.raises(ImportError) as info:
        CheckpointSerializable.load(saved)

    message = str(info.value)

    assert 'could not be recovered' in message
    assert 'invalid load key' in message, 'the unpickling failure is the cause and has to be in the message'
    assert '__main__:NotebookClass' in message
    assert 'while no daemon was running' in message, 'one of the two situations that still reach this'
    assert 'cloudpickle' in message, 'the other one'
    assert info.value.__cause__ is not None, 'the unpickling failure is the chained cause'

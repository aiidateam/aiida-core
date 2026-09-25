###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.engine.processes._class_identity`."""

import logging
import sys
import typing as t
from collections.abc import Callable
from types import ModuleType

import pytest

from aiida import orm
from aiida.common import callables, loaders
from aiida.common.exceptions import ConfigurationError
from aiida.engine import calcfunction
from aiida.engine.processes import _class_identity
from aiida.engine.processes.persistence import CheckpointSerializable


class ImportableSerializable(CheckpointSerializable):
    """Defined by this module, so its identifier resolves wherever this module can be imported."""


class NestedHolder:
    """Holds a class whose qualified name the loader's ``module:name`` identifier form cannot express."""

    class Nested(CheckpointSerializable):
        """Importable by following its qualified name, yet no identifier the loader builds reaches it."""


@calcfunction
def module_level_calcfunction(value: t.Any):
    """A process function this module defines, so the function that identifies its process resolves."""
    return value


def notebook_class(monkeypatch: pytest.MonkeyPatch):
    """Return a class bound in ``__main__``, as one defined in a notebook cell is.

    The binding is what makes the qualified name reachable in this interpreter, which is the situation of the
    kernel that defined it and not of any worker.
    """

    class NotebookClass(CheckpointSerializable):
        """Stands in for a class defined in a notebook cell."""

    NotebookClass.__module__ = '__main__'
    NotebookClass.__qualname__ = 'NotebookClass'
    NotebookClass.__name__ = 'NotebookClass'
    monkeypatch.setattr(sys.modules['__main__'], 'NotebookClass', NotebookClass, raising=False)

    return NotebookClass


UNIMPORTED_MODULE: t.Final = 'a_module_nothing_here_imported'
"""A module name nothing here imports, so following it would mean importing it."""

assert UNIMPORTED_MODULE not in sys.modules, 'the name has to be one nothing in this interpreter imported'


def _identifier_of_a_class_defined_in_a_function() -> str:
    """Return an identifier whose qualified name carries ``<locals>``."""

    def make() -> type:
        class Local:
            """Defined inside a function, so no import can follow its qualified name."""

        return Local

    identifier: str = f'{__name__}:{make().__qualname__}'

    assert '<locals>' in identifier

    return identifier


LOCAL_CLASS_IDENTIFIER: t.Final = _identifier_of_a_class_defined_in_a_function()


def identity_of(cls, monkeypatch: pytest.MonkeyPatch, worker_paths):
    """Return what would be recorded for ``cls`` by a worker searching ``worker_paths``."""
    monkeypatch.setattr(_class_identity, 'get_daemon_import_paths', lambda: worker_paths)

    return _class_identity.identity_policy.recorded_for(value=cls, loader=loaders.get_object_loader())


@pytest.mark.parametrize(
    'worker_paths',
    (
        pytest.param(tuple(sys.path), id='a-daemon-started-from-here'),
        # Nothing believable is recorded, and the name still resolves here, so it is kept rather than the class
        # being pickled into the checkpoint of every ordinary process while a daemon is misconfigured.
        pytest.param(('/somewhere/else',), id='a-daemon-from-another-installation'),
    ),
)
def test_class_identity_uses_a_name_the_worker_resolves(monkeypatch: pytest.MonkeyPatch, worker_paths):
    identity = identity_of(ImportableSerializable, monkeypatch, worker_paths)

    assert identity.name == f'{__name__}:ImportableSerializable'
    assert identity.class_bytes is None


def test_class_identity_carries_a_class_the_worker_cannot_import(
    user_serializable: type[CheckpointSerializable], monkeypatch: pytest.MonkeyPatch, worker_without: tuple[str, ...]
):
    identity = identity_of(user_serializable, monkeypatch, worker_without)

    assert callables.loads(identity.class_bytes) is user_serializable


def test_class_identity_of_a_process_function_stays_a_name(monkeypatch: pytest.MonkeyPatch):
    """A process function is judged by the function that identifies it. Its class is built for each function and no
    name refers to that class, so judging the class itself would carry every process function ever run into
    its own checkpoint, and change its node hash with it.
    """
    identity = identity_of(module_level_calcfunction.process_class, monkeypatch, tuple(sys.path))

    assert identity.name.endswith(':module_level_calcfunction')
    assert identity.class_bytes is None


def test_class_identity_keeps_the_name_when_the_class_cannot_be_serialized(monkeypatch: pytest.MonkeyPatch):
    """A class defined inside a function closes over whatever that function held, which may be a node, and a node
    cannot be pickled. Failing the checkpoint over it would break a process that used to run.
    """
    node = orm.Int(1).store()

    class ClosesOverANode(CheckpointSerializable):
        """Its methods hold a node, so serializing the class pulls that node in with it."""

        def value(self):
            return node

    class ClosesOverNothing(CheckpointSerializable):
        """Defined in the same place, and nothing stops it being written into the checkpoint."""

    # No name reaches either, so both get as far as being offered to the serializer. Only one survives it, which is
    # what pins the failure to the handler rather than to the branch never being reached.
    refused = identity_of(ClosesOverANode, monkeypatch, tuple(sys.path))
    carried = identity_of(ClosesOverNothing, monkeypatch, tuple(sys.path))

    assert refused.class_bytes is None
    assert refused.name == f'{__name__}:{ClosesOverANode.__qualname__}'
    assert carried.class_bytes is not None


def test_class_identity_of_a_class_no_identifier_reaches(monkeypatch: pytest.MonkeyPatch):
    """``identify_object`` builds ``module:name`` and then resolves it, which fails for a class defined inside a
    function. Saving a checkpoint is not where that should surface.
    """

    class Local(CheckpointSerializable):
        """Nothing in its module is bound to this name, so no identifier reaches it."""

    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(Local)

    identity = identity_of(Local, monkeypatch, None)

    assert identity.name == f'{__name__}:{Local.__qualname__}'
    assert callables.loads(identity.class_bytes).__qualname__ == Local.__qualname__


def test_class_identity_carries_a_nested_class_without_a_daemon(monkeypatch: pytest.MonkeyPatch):
    """``resolves_here`` follows a dotted qualified name and succeeds, while the loader builds ``module:name`` and
    resolves that, which reaches nothing. Only both results together settle whether a name is worth keeping.
    """
    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(NestedHolder.Nested)

    assert callables.resolves_here(NestedHolder.Nested)

    identity = identity_of(NestedHolder.Nested, monkeypatch, None)

    assert identity.name == f'{__name__}:NestedHolder.Nested'
    assert callables.loads(identity.class_bytes) is NestedHolder.Nested


def test_class_identity_carries_a_main_class_without_a_daemon(monkeypatch: pytest.MonkeyPatch):
    """Submitting while the daemon is down is ordinary: the task waits in the broker and a worker rebuilds the
    process from the checkpoint once it starts. ``__main__`` is that worker's own entry point, so the name that
    would otherwise be kept reaches nothing there.
    """

    cls = notebook_class(monkeypatch)

    identity = identity_of(cls, monkeypatch, None)

    assert identity.name == '__main__:NotebookClass'

    # ``loads`` hands back this very class rather than rebuilding one, since ``cloudpickle`` tracks a class it
    # pickled by value within the interpreter that pickled it. So this says the bytes are valid and carry this
    # class and nothing else. That another interpreter rebuilds a class from them is
    # ``test_dumps_carries_the_module`` in ``tests/common/test_callables.py``, which loads in a subprocess,
    # and ``test_workchain_defined_in_main``, which loads in a daemon worker.
    assert callables.loads(identity.class_bytes) is cls


@pytest.mark.parametrize(
    ('worker_paths', 'identifier', 'resolves'),
    (
        # Nothing is recorded about the worker, so nothing is claimed about it, which is how this behaved before.
        pytest.param(None, 'json:dumps', True, id='nothing-recorded-about-the-worker'),
        # A loader of somebody else's may use a form this cannot read, and guessing would be worse than trusting it.
        pytest.param((), 'an-opaque-identifier', True, id='a-form-this-cannot-read'),
        # Judging it would mean importing the module, which runs its code for the sake of a check.
        pytest.param(None, f'{UNIMPORTED_MODULE}:Thing', True, id='a-module-this-interpreter-lacks'),
        # The control for the row below: the same module, a qualified name that does lead somewhere.
        pytest.param(tuple(sys.path), f'{__name__}:module_level_calcfunction', True, id='a-name-that-resolves'),
        # A class defined inside a function carries ``<locals>``, a path no import can follow, here or anywhere.
        pytest.param(tuple(sys.path), LOCAL_CLASS_IDENTIFIER, False, id='a-qualname-going-nowhere'),
    ),
)
def test_resolves_for_worker(
    worker_paths: tuple[str, ...] | None, identifier: str, resolves: bool, monkeypatch: pytest.MonkeyPatch
):
    """Whether the worker gets the same object back from ``identifier``, over the cases that decide it."""
    monkeypatch.setattr(_class_identity, 'get_daemon_import_paths', lambda: worker_paths)

    assert _class_identity.identity_policy._resolves_for_worker(identifier=identifier) is resolves


def test_modules_to_carry_rejects_paths_that_lead_elsewhere(caplog: pytest.LogCaptureFixture):
    """The daemon is started by an interpreter that need not be this one: another checkout with its own virtual
    environment, or a stopped daemon whose file outlived the environment that wrote it. What this interpreter has
    loaded then bears no relation to what that one can import.
    """
    with caplog.at_level('WARNING'):
        carried = _class_identity.identity_policy._modules_to_carry(())

    # `None` rather than an empty mapping: with the latter the worker lacks nothing, which sends the callable
    # down the class-bytes branch carrying none of what it needs.
    assert carried is None
    assert 'do not lead back to the files' in caplog.text


def test_modules_to_carry_acts_on_a_plausible_one(
    importable_module: Callable[..., ModuleType], worker_without: tuple[str, ...]
):
    importable_module('plausible_lib', 'value = 1\n')

    carried = _class_identity.identity_policy._modules_to_carry(worker_without)

    assert 'plausible_lib' in carried
    assert len(carried) * 2 <= len(sys.modules), 'the ordinary result is a handful of modules'


def test_a_class_that_cannot_be_serialized_is_reported_once(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """This runs on every state transition, so a process whose class cannot be written would otherwise repeat the
    warning for as long as it runs.
    """
    node = orm.Int(1).store()

    class ClosesOverANode(CheckpointSerializable):
        """Its methods hold a node, so serializing the class pulls that node in with it."""

        def value(self):
            return node

    with caplog.at_level(logging.WARNING, logger=_class_identity.LOGGER.name):
        for _ in range(3):
            assert identity_of(ClosesOverANode, monkeypatch, tuple(sys.path)).class_bytes is None

    assert caplog.text.count('could not write the class of this process') == 1


def test_a_class_travelling_without_modules_is_reported_once(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """With no daemon running, nothing is known about the worker, so the class travels carrying no modules.

    Neither the refusal nor the mismatch warning covers this: a daemon started from here would load the class, so
    refusing is wrong, and nothing is recorded to contradict. Without the warning a worker started later from
    elsewhere fails on an import with nothing connecting it to this submission.
    """
    cls = notebook_class(monkeypatch)

    with caplog.at_level(logging.WARNING, logger=_class_identity.LOGGER.name):
        for _ in range(3):
            assert identity_of(cls, monkeypatch, None).class_bytes is not None

    assert caplog.text.count('no daemon has recorded the paths') == 1


def test_a_daemon_started_from_here_reports_nothing(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    """The control for the test above: with a daemon's own paths recorded, the modules are worked out and the
    warning would be noise on every ordinary submission.
    """
    cls = notebook_class(monkeypatch)

    with caplog.at_level(logging.WARNING, logger=_class_identity.LOGGER.name):
        identity_of(cls, monkeypatch, tuple(sys.path))

    assert 'no daemon has recorded the paths' not in caplog.text


def test_the_refusal_to_carry_is_reported_once_per_path_list(caplog: pytest.LogCaptureFixture):
    """This runs on every checkpoint of every process, so a deployment whose reported paths belong to another machine
    would otherwise repeat the warning on every state transition it makes.
    """
    elsewhere = ('/srv/pod/venv/lib/python3.12/site-packages',)

    with caplog.at_level(logging.WARNING, logger=_class_identity.LOGGER.name):
        for _ in range(3):
            assert _class_identity.identity_policy._modules_to_carry(elsewhere) is None

    assert caplog.text.count('do not lead back to the files') == 1


def submit_check_for(cls, monkeypatch, worker_paths):
    """Run the policy's check against a worker searching ``worker_paths``.

    That ``Runner.submit`` is what calls it is pinned by ``test_submit_refuses_a_class_the_worker_could_not_load``,
    since nothing here would notice the call going missing.
    """
    monkeypatch.setattr(_class_identity, 'get_daemon_import_paths', lambda: worker_paths)

    _class_identity.identity_policy.refuse_if_the_worker_cannot_load(value=cls, loader=loaders.get_object_loader())


def test_a_class_that_has_to_travel_refuses_a_daemon_from_another_installation(monkeypatch: pytest.MonkeyPatch):
    """Carrying a class whose modules cannot be worked out defers the failure to the worker, where the cause is an
    import error naming a module the submitter never mentioned. The submission is refused instead, where the
    ``verdi daemon restart`` that fixes it can still be run.
    """

    cls = notebook_class(monkeypatch)

    with pytest.raises(ConfigurationError, match=r'.*lead to another installation.*verdi daemon restart.*'):
        submit_check_for(cls, monkeypatch, ('/somewhere/else',))


def test_a_class_that_has_to_travel_is_still_recorded_for_a_local_run(monkeypatch: pytest.MonkeyPatch):
    """Recording runs for a process running here too, where the daemon's environment decides nothing. Refusing
    there would take every locally run class defined in a test or a cell with it.
    """

    cls = notebook_class(monkeypatch)

    identity = identity_of(cls, monkeypatch, ('/somewhere/else',))

    assert identity.name == '__main__:NotebookClass'
    assert identity.class_bytes is not None


def test_a_name_the_worker_resolves_survives_a_daemon_from_another_installation(monkeypatch: pytest.MonkeyPatch):
    """The refusal has to reach only the classes that have to travel. Everything with a name behaves as it always
    did against such a daemon, which is what keeps an ordinary plugin submittable while one is misconfigured.
    """
    submit_check_for(ImportableSerializable, monkeypatch, ('/somewhere/else',))  # does not raise


def test_nothing_recorded_about_the_worker_refuses_nothing(monkeypatch: pytest.MonkeyPatch):
    """A daemon may yet be started from here, so submitting before starting one keeps working."""

    cls = notebook_class(monkeypatch)

    submit_check_for(cls, monkeypatch, None)  # does not raise


def test_a_daemon_from_this_installation_refuses_nothing(monkeypatch: pytest.MonkeyPatch):
    """The ordinary case, and the one a refusal must never reach: a class defined in a cell submits to a daemon
    started from here, because the modules it needs are worked out from that daemon's own paths.
    """
    cls = notebook_class(monkeypatch)

    submit_check_for(cls, monkeypatch, tuple(sys.path))  # does not raise

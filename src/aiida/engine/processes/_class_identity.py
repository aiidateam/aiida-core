###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""What a checkpoint records so that the daemon worker reading it gets the process class back.

A name suffices whenever the worker resolves it to the same object. Where it does not, the class itself has to
travel, and deciding between the two is the whole of this module.

``ClassIdentity`` and ``identity_policy`` are what the rest of ``aiida.engine`` uses. Everything else carries a
leading underscore, including the two classes, because it is how that decision is reached rather than part of it.
"""

from __future__ import annotations

import contextlib
import dataclasses
import logging
import sys
import typing as t
from functools import partial
from types import ModuleType

from aiida.common import callables, loaders
from aiida.common.exceptions import ConfigurationError
from aiida.common.log import AIIDA_LOGGER
from aiida.engine.daemon.client import get_daemon_import_paths

LOGGER: t.Final[logging.Logger] = AIIDA_LOGGER.getChild('persistence')


class _WarnOnce:
    """Emit each message once per key, for as long as the interpreter runs.

    Identifying a class runs on every state transition of every process, so a warning about a deployment that
    stays misconfigured would be emitted on every one of them.
    """

    def __init__(self) -> None:
        self._seen: set[t.Hashable] = set()

    def __call__(self, key: t.Hashable, message: str, *args: t.Any) -> None:
        """Emit ``message`` the first time this is called with ``key``, and never again for that key."""
        if key in self._seen:
            return

        self._seen.add(key)
        LOGGER.warning(message, *args)

    def reset(self) -> None:
        """Forget which keys have been emitted, so that a test can watch a warning it has already provoked."""
        self._seen.clear()


@dataclasses.dataclass(frozen=True)
class _RecordPlan:
    """What a checkpoint is to record for a class, decided before anything is pickled.

    Both what gets written and whether a submission is refused follow from this, so the ordering of the checks
    behind it lives in one place.
    """

    name: str
    """The identifier the loader produced, or a module and qualified name where it produced none."""

    carry: dict[str, ModuleType] | None
    """The modules to write alongside the class, or ``None`` to keep the name and carry nothing."""

    modules_unknown: bool
    """Whether the class has to travel and the modules it needs cannot be worked out.

    A worker handed such a checkpoint fails on an import the submission never mentioned, which is why
    :meth:`_IdentityPolicy.refuse_if_the_worker_cannot_load` exists.
    """


@dataclasses.dataclass(frozen=True)
class ClassIdentity:
    """What a checkpoint records so that the worker reading it gets the process class back."""

    name: str
    """The identifier the loader produced, or a module and qualified name where it produced none."""

    class_bytes: bytes | None
    """The class itself, present only where ``name`` would not reach it for the worker."""


class _IdentityPolicy:
    """Resolves what a checkpoint records for a class, and warns once about what it had to give up on."""

    def __init__(self) -> None:
        self._warn: _WarnOnce = _WarnOnce()

    def reset_warnings(self) -> None:
        """Forget what has been warned about, so that a test can observe a warning already provoked.

        The memory is interpreter-wide by design, since the point is to warn once however many processes run.
        """
        self._warn.reset()

    @staticmethod
    def _qualname_leads_nowhere_here(*, module_name: str, qualname: str) -> bool:
        """Return whether following ``qualname`` through ``module_name`` is known to reach nothing.

        A module this interpreter has not loaded is not judged: importing it to find out would run its code for the
        sake of a check, and the paths recorded for the daemon settle the same question without one. ``False`` is
        therefore both "reaches something" and "not established", which is all the caller needs of it.
        """
        resolved: t.Any = sys.modules.get(module_name)

        if resolved is None:
            return False

        for attribute in qualname.split(sep='.'):
            resolved = getattr(resolved, attribute, None)

            if resolved is None:
                return True

        return False

    def _resolves_for_worker(self, identifier: str) -> bool:
        """Return whether the worker reading this checkpoint back resolves ``identifier`` to the same object.

        An identifier is a module and an attribute path within it, and both halves can fail. The module may be
        one the worker cannot import, and the attribute path may lead nowhere: a class defined inside a function carries
        ``<locals>`` in its qualified name, which no import can follow, here or anywhere.
        """
        module_name, separator, qualname = identifier.partition(':')

        # A loader of somebody else's may use a form this cannot read, and guessing would be worse than trusting it.
        if not separator:
            return True

        # ``__main__`` is the entry point of whichever interpreter is running, so this name refers to another module in
        # every worker, whatever its paths turn out to be.
        if module_name == '__main__':
            return False

        if self._qualname_leads_nowhere_here(module_name=module_name, qualname=qualname):
            return False

        paths: tuple[str, ...] | None = get_daemon_import_paths()

        if paths is None:
            return True

        return callables.module_resolves_in(module_name=module_name, search_paths=paths)

    def _modules_to_carry(self, paths: tuple[str, ...] | None) -> dict[str, ModuleType] | None:
        """Return the modules the carried class has to bring for an interpreter searching ``paths``.

        ``None`` covers the cases with no believable result, either because nothing is recorded about the worker
        or because what is recorded cannot be true. It differs from an empty mapping, where the worker lacks
        nothing: a caller that cannot carry modules has to keep the name, since process class bytes without them
        would fail to load there.

        ``paths`` is itself optional for the same reason, rather than to let a caller skip the call: a daemon that
        recorded none and a daemon whose paths lead somewhere else produce the same result here, so both belong to
        this function rather than to a test the caller repeats.
        """
        if paths is None:
            return None

        # The daemon is started by an interpreter that need not be this one: another checkout with its own virtual
        # environment, or a stopped daemon whose file outlived the environment that wrote it, since the file is read
        # whenever it exists. What this interpreter has loaded then bears no relation to what that one can import,
        # and every module would be counted as missing.
        if not callables.module_resolves_in(module_name='aiida', search_paths=paths):
            self._warn(
                paths,
                'the import paths recorded for the daemon do not lead back to the files this interpreter is '
                'running, so the daemon runs another installation or another machine. A process class defined in a '
                'notebook or a script may fail to load there; restart the daemon from this environment.',
            )

            return None

        return callables.modules_unimportable_by(can_import=partial(callables.module_resolves_in, search_paths=paths))

    @staticmethod
    def _identifier_of(*, value: type, loader: loaders.ObjectLoader) -> str | None:
        """Return the identifier the loader builds for ``value``, or ``None`` where it builds none."""
        with contextlib.suppress(ImportError, AttributeError):
            return loader.identify_object(obj=value)

        return None

    def _plan_for(self, *, value: type, loader: loaders.ObjectLoader) -> _RecordPlan:
        """Return what a checkpoint is to record for ``value``, before anything is pickled.

        Its identifier suffices whenever the interpreter reading this back resolves that identifier to the same
        object. A class defined in a notebook or a script has no such identifier, since its module is the entry point
        of whichever interpreter is running, so the class travels in the checkpoint instead, together with the
        modules it needs and that worker lacks.

        The identifier is what gets checked, because a process built from a function is identified by that function,
        while the class built for it carries a name of its own that nothing refers to.
        """
        identifier: str | None = self._identifier_of(value=value, loader=loader)

        # Written unverified, so that a checkpoint still records what it holds when read by a human. A class the
        # loader cannot identify at all still gets a name here; the process class bytes are what bring it back.
        name: str = identifier or f'{value.__module__}:{value.__qualname__}'

        if identifier is not None and self._resolves_for_worker(identifier=identifier):
            LOGGER.debug('`%s` resolves for the worker, so the checkpoint records it and carries no class', identifier)
            return _RecordPlan(name=name, carry=None, modules_unknown=False)

        paths: tuple[str, ...] | None = get_daemon_import_paths()
        needed: dict[str, ModuleType] | None = self._modules_to_carry(paths=paths)

        if needed is None and identifier is not None and callables.resolves_here(value=value):
            # Nothing believable is recorded about the worker, so the process class bytes might carry too little
            # there. The name is what this recorded before the worker was ever consulted, and it is worth keeping
            # only where some interpreter could follow it: ``__main__`` resolves elsewhere, and a nested qualified
            # name is one the loader's own ``module:name`` form cannot express.
            LOGGER.debug('nothing believable is recorded about the worker, so `%s` travels as a name', identifier)
            return _RecordPlan(name=name, carry=None, modules_unknown=False)

        if needed is None and paths is None:
            # A class travelling with no modules is the one case that neither refuses nor carries what it needs: a
            # worker started later from elsewhere then fails on an import with nothing to connect it to this
            # submission. Refusing is wrong, since a daemon started from here would load it.
            self._warn(
                'no-daemon-recorded',
                'no daemon has recorded the paths its workers import from, so `%s` travels without the modules it '
                'may need there. Start the daemon from this environment before submitting, or the process may fail '
                'in the worker on a module only this interpreter can import.',
                name,
            )

        return _RecordPlan(
            name=name,
            carry={} if needed is None else needed,
            # A daemon that recorded nothing leaves nothing to contradict, and one may yet start from here.
            modules_unknown=needed is None and paths is not None,
        )

    def refuse_if_the_worker_cannot_load(self, *, value: type, loader: loaders.ObjectLoader) -> None:
        """Raise where submitting ``value`` would put an unloadable class in front of a worker.

        :raises ConfigurationError: if the class has to travel and the modules it needs cannot be worked out.
        """
        if not self._plan_for(value=value, loader=loader).modules_unknown:
            return

        msg = (
            f'`{value.__module__}:{value.__qualname__}` has no name a daemon worker resolves, so its class has to '
            f'travel in the checkpoint, and the modules it needs cannot be worked out: the import paths recorded '
            f'for the daemon lead to another installation. Run `verdi daemon restart` from this environment, or '
            f'give the class an entry point.'
        )
        raise ConfigurationError(msg)

    def recorded_for(self, *, value: type, loader: loaders.ObjectLoader) -> ClassIdentity:
        """Record how the worker is to get ``value`` back."""
        plan: _RecordPlan = self._plan_for(value=value, loader=loader)
        name: str = plan.name

        if plan.carry is None:
            return ClassIdentity(name=name, class_bytes=None)

        # ``cloudpickle`` writes a class that no module can provide by value, once it is given what to carry.
        try:
            class_bytes: bytes = callables.dumps(value=value, carry=plan.carry.values())
        except TypeError as exception:
            # A class defined inside a function closes over whatever that function held, which may be a node, and
            # nodes cannot be pickled. Keeping the name leaves such a process exactly as it was, working wherever
            # that name reaches and failing where it never did, so the warning is what gives the eventual import
            # error in the worker a cause.
            self._warn(
                name,
                'could not write the class of this process into its checkpoint, so `%s` has to be importable '
                'wherever the checkpoint is read back: %s',
                name,
                exception,
            )

            return ClassIdentity(name=name, class_bytes=None)

        LOGGER.debug(
            'the class `%s` travels in the checkpoint as %d bytes, carrying %d modules',
            name,
            len(class_bytes),
            len(plan.carry),
        )

        return ClassIdentity(name=name, class_bytes=class_bytes)


identity_policy: t.Final[_IdentityPolicy] = _IdentityPolicy()

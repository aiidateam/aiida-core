###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities to say which installed distribution a module comes from, and which code that distribution holds."""

from __future__ import annotations

import functools
import pathlib
import sys
import typing as t
from collections import abc

import importlib_metadata

__all__ = ('Distribution', 'distribution_of')


class Distribution(t.NamedTuple):
    """What is known about the distribution a module comes from, all of it optional.

    The three travel together because they answer one question, what a reader would have to install to get the
    module back, and each of them can be unknown on its own.
    """

    name: str | None = None
    version: str | None = None
    commit: str | None = None


@functools.cache
def _packages_distributions() -> abc.Mapping[str, list[str]]:
    """Cache around :func:`importlib_metadata.packages_distributions`.

    Building the mapping reads the metadata of every installed distribution and takes around 200ms, against 0.3ms for
    the lookup it serves, and what is installed does not change while the interpreter runs.
    """
    return importlib_metadata.packages_distributions()


class EditableRoot(t.NamedTuple):
    """A directory an editable install puts on ``sys.path``, and the distribution that put it there."""

    name: str
    version: str
    directory: str


@functools.cache
def _editable_roots() -> tuple[EditableRoot, ...]:
    """Return every directory an editable install adds to ``sys.path``, and what put it there.

    A package installed in editable mode can be missing from what :func:`importlib_metadata.packages_distributions`
    reports, since nothing of it is installed for that mapping to find. The ``.pth`` file that makes it importable at
    all is then the only record that it belongs to a distribution. Only distributions that PEP 610 marks as editable
    are read, which is both the cheaper walk and the one that cannot match somebody else's ``.pth``.
    """
    roots = []

    for distribution in importlib_metadata.distributions():
        origin = distribution.origin

        if not getattr(getattr(origin, 'dir_info', None), 'editable', False):
            continue

        name, version = distribution.metadata['Name'], distribution.version

        for entry in distribution.files or []:
            if not str(entry).endswith('.pth'):
                continue

            try:
                content = pathlib.Path(str(distribution.locate_file(entry))).read_text(encoding='utf8')
            except OSError:
                continue

            for line in content.splitlines():
                stripped = line.strip()

                # A line in a ``.pth`` file is either a directory to add or code to run, and a package that is put
                # there by code, as ``setuptools`` does through a finder, is in the mapping anyway.
                if not stripped or stripped.startswith(('import ', 'import\t', '#')):
                    continue

                roots.append(EditableRoot(name, version, str(pathlib.Path(stripped).resolve())))

    return tuple(roots)


def _editable_distribution(top_level: str) -> Distribution:
    """Return the distribution that puts ``top_level`` on ``sys.path`` in editable mode, if one does.

    :param top_level: The name of the top level package to account for.
    :returns: What is known about it, empty if no editable install accounts for it.
    """
    module = sys.modules.get(top_level)
    origin: str | None = getattr(getattr(module, '__spec__', None), 'origin', None)

    if origin is None:
        return Distribution()

    # The directory holding the package, which is what a ``.pth`` line has to name for the import to have worked.
    directory = str(pathlib.Path(origin).resolve().parent.parent)

    for root in _editable_roots():
        if root.directory == directory:
            return Distribution(root.name, root.version, _commit_of(root.name))

    return Distribution()


def distribution_of(module: str | None) -> Distribution:
    """Return what is known about the distribution that provides ``module``.

    What a module is imported as and what it is installed as are different names: ``yaml`` comes from ``PyYAML`` and
    ``aiida`` from ``aiida-core``. Only the latter is something a reader can install, so it is worth resolving while
    the package is still here; by the time something needs it, it may well be gone.

    :param module: The dotted name of the module to account for, or ``None`` to ask about nothing.
    :returns: What is known about it, empty where the module belongs to no installed distribution.
    """
    if module is None:
        return Distribution()

    top_level = module.split('.', maxsplit=1)[0]

    # Several distributions can contribute to one namespace package, and then none of them provides the module on its
    # own. The import name is the fallback because it is also the distribution name often enough to be worth asking.
    # One distribution reported more than once, which an editable install is, is not that case, which is why this
    # asks how many distinct ones there are.
    provides = set(_packages_distributions().get(top_level, []))
    name = provides.pop() if len(provides) == 1 else top_level

    try:
        return Distribution(name, importlib_metadata.version(name), _commit_of(name))
    except importlib_metadata.PackageNotFoundError:
        return _editable_distribution(top_level)


def _commit_of(distribution: str) -> str | None:
    """Return the commit ``distribution`` was installed from, or ``None`` if it did not come from a repository.

    A version does not say which code is installed when a distribution is built from a branch: every commit on
    ``main`` calls itself ``2.10.0.dev0``. PEP 610 has the installer record what was actually checked out, of which
    the resolved commit is the half worth keeping: the revision that was asked for can be a branch and move.

    :param distribution: The name of the distribution to account for.
    :returns: The commit, or ``None``.
    """
    try:
        origin = importlib_metadata.distribution(distribution).origin
    except importlib_metadata.PackageNotFoundError:
        return None

    return t.cast('str | None', getattr(getattr(origin, 'vcs_info', None), 'commit_id', None))

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.distributions` module."""

import importlib.machinery
import sys
import types

import importlib_metadata

from aiida.common import distributions


def test_distribution_of_an_installed_package():
    """Test that a package installed under a different name than it is imported under names the distribution."""
    provider = distributions.distribution_of('yaml')

    assert (provider.name, provider.version) == ('PyYAML', importlib_metadata.version('PyYAML'))


def test_distribution_of_the_standard_library():
    """Test that a module no distribution provides is answered with nothing rather than with its import name."""
    assert distributions.distribution_of('json') == distributions.Distribution()


def test_distribution_reported_more_than_once(monkeypatch):
    """Test that one distribution reported several times still names that distribution.

    ``packages_distributions`` lists a distribution once per path entry that provides the package, so an install in
    editable mode is reported twice, and counting entries rather than distinct names throws the answer away.
    """

    def version(name):
        if name == 'demo-editable':
            return '0.1.0'
        raise importlib_metadata.PackageNotFoundError(name)

    monkeypatch.setattr(distributions, '_packages_distributions', lambda: {'demo': ['demo-editable'] * 2})
    monkeypatch.setattr(distributions.importlib_metadata, 'version', version)
    monkeypatch.setattr(distributions, '_commit_of', lambda _: None)

    assert distributions.distribution_of('demo.sub') == distributions.Distribution('demo-editable', '0.1.0', None)


def test_distribution_of_an_editable_install(monkeypatch, tmp_path):
    """Test that a package put on ``sys.path`` by a ``.pth`` file is traced back to the distribution that did it.

    Nothing of such a package is installed for ``packages_distributions`` to find, so that file is the only record
    that it belongs to a distribution at all.
    """
    package = tmp_path / 'demo'
    package.mkdir()
    (package / '__init__.py').write_text('')

    module = types.ModuleType('demo')
    module.__spec__ = importlib.machinery.ModuleSpec('demo', None, origin=str(package / '__init__.py'))

    monkeypatch.setitem(sys.modules, 'demo', module)
    monkeypatch.setattr(distributions, '_packages_distributions', dict)
    root = distributions.EditableRoot('demo-editable', '0.1.0', str(tmp_path))
    monkeypatch.setattr(distributions, '_editable_roots', lambda: (root,))
    monkeypatch.setattr(distributions, '_commit_of', lambda _: None)

    assert distributions.distribution_of('demo.sub') == distributions.Distribution('demo-editable', '0.1.0', None)


def test_distribution_of_a_package_nothing_accounts_for(monkeypatch):
    """Test that a package no distribution accounts for is answered with nothing, rather than with a guess."""
    monkeypatch.setattr(distributions, '_packages_distributions', dict)
    monkeypatch.setattr(distributions, '_editable_roots', tuple)

    assert distributions.distribution_of('json')[:2] == (None, None)


def test_commit_of_a_distribution_installed_from_a_repository(monkeypatch):
    """Test that the commit is reported for a distribution built from a repository rather than a release.

    A version does not identify the code in that case: every commit on a branch reports the same one. Only the
    resolved commit is kept, since the revision that was asked for can be a branch and move under the answer.
    """

    class Distribution:
        """Stands in for a distribution whose installer recorded where it came from, as PEP 610 asks."""

        origin = types.SimpleNamespace(
            url='https://github.com/aiidateam/aiida-core.git',
            vcs_info=types.SimpleNamespace(vcs='git', commit_id='a' * 40, requested_revision='main'),
        )

    monkeypatch.setattr(distributions.importlib_metadata, 'distribution', lambda _: Distribution())

    assert distributions._commit_of('demo') == 'a' * 40


def test_commit_of_a_distribution_installed_from_a_release(monkeypatch):
    """Test that a distribution that did not come from a repository reports no commit."""

    class Distribution:
        """Stands in for an ordinary wheel, which PEP 610 records nothing for."""

        origin = None

    monkeypatch.setattr(distributions.importlib_metadata, 'distribution', lambda _: Distribution())

    assert distributions._commit_of('demo') is None


def test_commit_of_a_distribution_that_is_not_installed():
    """Test that asking about something that is not installed is answered rather than raised."""
    assert distributions._commit_of('no-such-distribution') is None

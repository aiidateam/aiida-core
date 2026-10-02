###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for inheritance-based resolution of class queries to stored node types."""

import pytest

from aiida.orm import Data, Node
from aiida.orm.utils.node_inheritance import node_type_filter, resolve_node_types


class UnregisteredBase(Data):
    """Base class without an entry point, acting purely as a query target."""


class RegisteredChild(UnregisteredBase):
    """Concrete implementation standing in for a registered plugin."""


class OtherChild(Data):
    """Concrete implementation outside the base under query."""


class UnrelatedNamespaceChild(UnregisteredBase):
    """Subclass whose stored type shares nothing but the base class with its siblings.

    The module of a class determines its type string, so defining this class here gives it a type string
    in the same namespace as the other test doubles. Namespace similarity must never cause inclusion:
    only the explicit candidate collection decides membership.
    """


class OrthogonalMixin:
    """Plain mixin without any node semantics."""


class MixinChild(RegisteredChild, OrthogonalMixin):
    """Implementation with multiple inheritance, selected through its node parent."""


@pytest.fixture
def candidates():
    """Candidate collection standing in for the registered implementations."""
    return (RegisteredChild, OtherChild, UnrelatedNamespaceChild, MixinChild)


def test_unregistered_base_selects_registered_subclasses(candidates):
    """An unregistered base selects its registered subclasses without needing an entry point itself."""
    selected = resolve_node_types(UnregisteredBase, subclassing=True, candidates=candidates)
    assert RegisteredChild.class_node_type in selected
    assert UnrelatedNamespaceChild.class_node_type in selected
    assert MixinChild.class_node_type in selected
    assert OtherChild.class_node_type not in selected
    assert UnregisteredBase.class_node_type not in selected


def test_unrelated_class_with_similar_namespace_excluded(candidates):
    """A class that merely shares a namespace prefix with candidates is not selected."""

    class SimilarNamespace(Data):
        pass

    selected = resolve_node_types(SimilarNamespace, subclassing=True, candidates=candidates)
    assert selected == ()


def test_subclass_with_unrelated_namespace_included():
    """A subclass is selected through inheritance even if its stored type shares no namespace."""

    # The module determines the stored type, so it has to be set at creation: type strings are derived from it.
    Elsewhere = type('Elsewhere', (Data,), {'__module__': 'some.third.party.plugin'})  # noqa: N806
    type_string = Elsewhere.class_node_type
    assert not type_string.startswith('tests.')

    selected = resolve_node_types(Data, subclassing=True, candidates=(Elsewhere,))
    assert selected == (type_string,)


def test_multiple_inheritance_without_duplicates(candidates):
    """A multiply-inherited implementation contributes a single stored identity."""
    selected = resolve_node_types(Data, subclassing=True, candidates=candidates)
    assert len(selected) == len(set(selected))
    assert MixinChild.class_node_type in selected
    # Selecting through either the node parent or a grandparent finds the same identity, exactly once
    for base in (RegisteredChild, UnregisteredBase):
        through_parent = resolve_node_types(base, subclassing=True, candidates=candidates)
        assert through_parent.count(MixinChild.class_node_type) == 1
    # Listing a candidate twice still yields a single identity
    duplicated = resolve_node_types(Data, subclassing=True, candidates=(*candidates, MixinChild))
    assert duplicated == selected


def test_selection_is_deterministic_and_deduplicated(candidates):
    """The selection is a sorted tuple of unique identifiers regardless of candidate order."""
    selected = resolve_node_types(Data, subclassing=True, candidates=candidates)
    assert isinstance(selected, tuple)
    assert tuple(sorted(selected)) == selected
    reversed_selected = resolve_node_types(Data, subclassing=True, candidates=tuple(reversed(candidates)))
    assert reversed_selected == selected


def test_exact_query_excludes_subclasses(candidates):
    """Exact queries match only the requested class itself."""
    selected = resolve_node_types(UnregisteredBase, subclassing=False, candidates=candidates)
    assert selected == (UnregisteredBase.class_node_type,)


def test_exact_query_non_storable_base_is_empty():
    """Exact queries for a non-storable base match nothing."""

    class AbstractBase(Data):
        _storable = False

    assert resolve_node_types(AbstractBase, subclassing=False, candidates=(AbstractBase,)) == ()


def test_empty_family_matches_nothing(candidates):
    """A base without any registered subclasses selects nothing, exactly or with subclassing."""

    class LonelyBase(Data):
        pass

    assert resolve_node_types(LonelyBase, subclassing=True, candidates=candidates) == ()
    assert resolve_node_types(LonelyBase, subclassing=False, candidates=candidates) == (LonelyBase.class_node_type,)


def test_invalid_candidates_never_match(candidates):
    """Non-class entries and non-``Node`` classes do not become query members."""
    polluted = (*candidates, 'data.Data.', 42, None, int, dict)
    selected = resolve_node_types(Data, subclassing=True, candidates=polluted)
    assert selected == resolve_node_types(Data, subclassing=True, candidates=candidates)
    assert resolve_node_types(int, subclassing=True, candidates=candidates) == ()


def test_non_storable_candidates_excluded():
    """Abstract registrations that can never be stored contribute no stored types."""

    class AbstractRegistered(Data):
        _storable = False

    class ConcreteRegistered(AbstractRegistered):
        _storable = True

    selected = resolve_node_types(Data, subclassing=True, candidates=(AbstractRegistered, ConcreteRegistered))
    assert selected == (ConcreteRegistered.class_node_type,)


def test_node_type_filter_shapes():
    """The ``QueryBuilder`` filter uses exact identifiers and an explicit match-nothing fallback."""
    from aiida.orm import Code

    filt = node_type_filter(Code, subclassing=False)
    assert filt == {'==': Code.class_node_type}

    filt = node_type_filter(Data, subclassing=False)
    assert filt == {'==': Data.class_node_type}

    # An unregistered base without subclasses resolves to a match-nothing equality on its own type
    filt = node_type_filter(UnregisteredBase, subclassing=True)
    assert filt == {'==': UnregisteredBase.class_node_type}

    # A subclassing query over real entry points selects multiple exact types without namespace prefixes
    filt = node_type_filter(Code, subclassing=True)
    assert set(filt) == {'in'}
    assert len(filt['in']) == len(set(filt['in']))
    assert filt['in'] == sorted(filt['in'])
    assert all(isinstance(type_string, str) and type_string.endswith('.') for type_string in filt['in'])
    assert Code.class_node_type not in filt['in']
    assert 'data.core.code.installed.InstalledCode.' in filt['in']
    assert 'data.core.code.portable.PortableCode.' in filt['in']
    assert 'data.core.code.containerized.ContainerizedCode.' in filt['in']
    assert 'data.core.code.installed.shell.ShellCode.' in filt['in']


def test_base_node_matches_nothing_exact():
    """An exact query for the root ``Node`` matches nothing since bare nodes cannot be stored."""
    assert node_type_filter(Node, subclassing=False) == {'==': ''}

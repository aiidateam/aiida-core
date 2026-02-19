"""Tests for the :class:`aiida.orm.nodes.data.enum.Enum` data plugin."""

import enum

import pytest

from aiida.common import links
from aiida.orm import load_node
from aiida.orm.nodes.data.enum import EnumData


class DummyEnum(enum.Enum):
    """Dummy enum for testing."""

    OPTION_A = 'a'
    OPTION_B = 'b'


def test_construct():
    """Test the ``EnumData`` constructor."""
    instance = DummyEnum.OPTION_A
    node = EnumData(instance)

    assert isinstance(node, EnumData)
    assert not node.is_stored


@pytest.mark.parametrize('value', (42, 'string'))
def test_construct_invalid_type(value):
    """Test the ``EnumData`` constructor raises if member is not an enum."""
    with pytest.raises(TypeError, match=r'Got object of type .*, expecting .*.'):
        EnumData(value)


def test_load_node():
    """Test loading a stored ``EnumData`` node."""
    member = DummyEnum.OPTION_A
    node = EnumData(member)
    node.store()

    loaded = load_node(node.pk)
    assert isinstance(loaded, EnumData)
    assert loaded.is_stored


def test_name():
    """Test the ``name`` property."""
    member = DummyEnum.OPTION_A
    node = EnumData(member)
    assert node.name == member.name

    node.store()
    assert node.name == member.name

    loaded = load_node(node.pk)
    assert loaded.name == member.name


def test_value():
    """Test the ``value`` property."""
    member = DummyEnum.OPTION_A
    node = EnumData(member)
    assert node.value == member.value

    node.store()
    assert node.value == member.value

    loaded = load_node(node.pk)
    assert loaded.value == member.value


def test_get_enum():
    """Test the ``get_enum`` method."""
    member = DummyEnum.OPTION_A
    node = EnumData(member)
    assert node.get_enum() == DummyEnum

    node.store()
    assert node.get_enum() == DummyEnum

    loaded = load_node(node.pk)
    assert loaded.get_enum() == DummyEnum


def test_get_member():
    """Test the ``get_member`` method."""
    member = DummyEnum.OPTION_A
    node = EnumData(member)
    assert node.get_member() == member

    node.store()
    assert node.get_member() == member

    loaded = load_node(node.pk)
    assert loaded.get_member() == member


def test_get_member_module_not_importable():
    """Test the ``get_member`` property when the enum cannot be imported from the identifier."""
    member = DummyEnum.OPTION_A
    node = EnumData(member)
    node.base.attributes.set(EnumData.KEY_IDENTIFIER, 'aiida.common.links:NonExistingEnum')
    node.store()

    loaded = load_node(node.pk)

    with pytest.raises(ImportError):
        loaded.get_member()


def test_get_member_invalid_value(monkeypatch):
    """Test the ``get_member`` method when stored value is no longer valid for the class loaded from the identifier."""
    member = links.LinkType.RETURN
    node = EnumData(member).store()

    class ChangedLinkType(enum.Enum):
        """Change the definition of the :class:`aiida.common.links.LinkType`"""

        RETURN = 'different_return'

    # And then monkeypatch the :mod:`aiida.common.links` module with the mock enum.
    monkeypatch.setattr(links, 'LinkType', ChangedLinkType)

    loaded = load_node(node.pk)

    with pytest.raises(ValueError, match=r'The stored value `return` is no longer a valid value for the enum `.*`'):
        loaded.get_member()


def test_eq():
    """Test the ``__eq__`` implementation."""
    node_a = EnumData(DummyEnum.OPTION_A)
    node_b = EnumData(DummyEnum.OPTION_B)

    assert node_a == DummyEnum.OPTION_A
    assert node_a != DummyEnum.OPTION_B
    assert node_a == node_a  # noqa: PLR0124
    assert node_a != node_b
    assert node_a != DummyEnum.OPTION_A.value

    # If the identifier cannot be resolved, the equality should not raise but simply return ``False``.
    node_a.base.attributes.set(EnumData.KEY_IDENTIFIER, 'aiida.common.links:NonExistingEnum')
    assert node_a != DummyEnum.OPTION_A

    # If the value is incorrect for the resolved identifier, the equality should not raise but simply return ``False``.
    node_b.base.attributes.set(EnumData.KEY_VALUE, 'c')
    assert node_b != DummyEnum.OPTION_B

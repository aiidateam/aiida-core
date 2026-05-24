"""Tests for :mod:`aiida.cmdline.groups.dynamic`."""

import abc
import typing as t

import click
import pytest
from pydantic_core import PydanticUndefined

from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup
from aiida.common.pydantic import AiiDABaseModel, MetadataField


class CustomClass:
    """Test plugin class."""

    class CliModel(AiiDABaseModel):
        optional_type: t.Union[int, float] = MetadataField(title='Optional type')
        union_type: t.Union[int, float] = MetadataField(title='Union type')
        without_default: str = MetadataField(title='Without default')
        with_default: str = MetadataField(title='With default', default='default')
        with_default_factory: str = MetadataField(title='With default factory', default_factory=lambda: True)


class AbstractCustomClass(abc.ABC):
    """Abstract test plugin class that cannot be instantiated and so should not be exposed on the CLI."""

    @abc.abstractmethod
    def required(self) -> None:
        """An abstract method that prevents the class from being instantiated."""

    class CliModel(AiiDABaseModel):
        some_option: str = MetadataField(title='Some option')


class HiddenCustomClass:
    """Test plugin class that opts out of being exposed on the CLI."""

    cli_exposed = False

    class CliModel(AiiDABaseModel):
        some_option: str = MetadataField(title='Some option')


def test_list_options(entry_points):
    """Test :meth:`aiida.cmdline.groups.dynamic.DynamicEntryPointCommandGroup.list_options`."""
    entry_points.add(CustomClass, 'aiida.custom:custom')

    group = DynamicEntryPointCommandGroup(lambda *args, **kwargs: True, entry_point_group='aiida.custom')

    for option_decorators in group.list_options('custom'):
        option = option_decorators(lambda x: True).__click_params__[0]
        field = CustomClass.CliModel.model_fields[option.name]
        assert option.default == field.default_factory if field.default is PydanticUndefined else field.default
        assert option.type == t.get_args(field.annotation) or field.annotation


def test_list_commands_excludes_non_exposed(entry_points):
    """Test that abstract and non-exposed plugin classes are not listed as subcommands.

    Regression test for https://github.com/aiidateam/aiida-core/issues/7379: an abstract entry point class
    cannot be instantiated and so building its CLI options is not possible. Such classes (and any class that
    sets ``cli_exposed = False``) should silently be excluded instead of breaking the rendering of the group.
    """
    entry_points.add(CustomClass, 'aiida.custom:custom')
    entry_points.add(AbstractCustomClass, 'aiida.custom:abstract')
    entry_points.add(HiddenCustomClass, 'aiida.custom:hidden')

    group = DynamicEntryPointCommandGroup(lambda *args, **kwargs: True, entry_point_group='aiida.custom')
    ctx = click.Context(group)

    assert group.list_commands(ctx) == ['custom']


def test_get_command_non_exposed(entry_points):
    """Test that resolving an abstract or non-exposed entry point fails gracefully.

    Regression test for https://github.com/aiidateam/aiida-core/issues/7379: instead of raising an internal
    ``UnsupportedSchemaError`` while building the options, resolving such an entry point should be treated as
    an unknown command and raise the regular user-facing :class:`click.exceptions.UsageError`.
    """
    entry_points.add(CustomClass, 'aiida.custom:custom')
    entry_points.add(AbstractCustomClass, 'aiida.custom:abstract')
    entry_points.add(HiddenCustomClass, 'aiida.custom:hidden')

    group = DynamicEntryPointCommandGroup(lambda *args, **kwargs: True, name='create', entry_point_group='aiida.custom')
    ctx = click.Context(group)

    assert group.get_command(ctx, 'custom') is not None
    for cmd_name in ('abstract', 'hidden', 'non_existent'):
        with pytest.raises(click.exceptions.UsageError):
            group.get_command(ctx, cmd_name)

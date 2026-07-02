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


@pytest.fixture
def custom_group(entry_points):
    """A dynamic group with one concrete, one abstract, and one ``cli_exposed = False`` plugin registered."""
    entry_points.add(CustomClass, 'aiida.custom:custom')
    entry_points.add(AbstractCustomClass, 'aiida.custom:abstract')
    entry_points.add(HiddenCustomClass, 'aiida.custom:hidden')
    return DynamicEntryPointCommandGroup(lambda *args, **kwargs: True, name='create', entry_point_group='aiida.custom')


@pytest.mark.parametrize(
    'cmd_name, exposed',
    [
        pytest.param('custom', True, id='concrete'),
        pytest.param('abstract', False, id='abstract'),
        pytest.param('hidden', False, id='cli_exposed_false'),
        pytest.param('non_existent', False, id='unknown'),
    ],
)
def test_subcommand_exposure(custom_group, cmd_name, exposed):
    """Only exposed plugins are listed and resolvable; abstract / ``cli_exposed = False`` / unknown are excluded.

    Regression test for https://github.com/aiidateam/aiida-core/issues/7379: an abstract entry point cannot be
    instantiated, so building its CLI options raised ``UnsupportedSchemaError`` and broke rendering of the whole
    group. Such plugins must be silently dropped from the listing and resolve to the regular user-facing
    :class:`click.exceptions.UsageError` instead of an internal traceback.
    """
    ctx = click.Context(custom_group)
    assert (cmd_name in custom_group.list_commands(ctx)) is exposed
    if exposed:
        assert custom_group.get_command(ctx, cmd_name) is not None
    else:
        with pytest.raises(click.exceptions.UsageError):
            custom_group.get_command(ctx, cmd_name)

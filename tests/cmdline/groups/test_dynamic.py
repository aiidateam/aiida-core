"""Tests for :mod:`aiida.cmdline.groups.dynamic`."""

import typing as t

import click
import pytest
from pydantic_core import PydanticUndefined

from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup
from aiida.common.pydantic import AiiDABaseModel, MetadataField


class CustomClass:
    """Test plugin class."""

    class CliModel(AiiDABaseModel):
        optional_type: int | float = MetadataField(title='Optional type')
        union_type: int | float = MetadataField(title='Union type')
        without_default: str = MetadataField(title='Without default')
        with_default: str = MetadataField(title='With default', default='default')
        with_default_factory: str = MetadataField(title='With default factory', default_factory=lambda: True)


class NoCliModelCustomClass:
    """Test plugin class that does not support CLI-based creation (like the abstract base ``AbstractCode``)."""

    supports_cli_model = False


class HiddenCustomClass:
    """Test plugin class that supports creation but opts out of being listed on the CLI."""

    supports_cli_model = True
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


@pytest.mark.parametrize(
    'cmd_name, listed, resolvable',
    [
        pytest.param('custom', True, True, id='concrete'),
        pytest.param('no_cli_model', False, False, id='no_cli_model'),
        pytest.param('hidden', False, True, id='cli_exposed_false'),
        pytest.param('non_existent', False, False, id='unknown'),
    ],
)
def test_subcommand_exposure(entry_points, cmd_name, listed, resolvable):
    """Listing is gated on ``supports_cli_model`` *and* ``cli_exposed``; resolution only on ``supports_cli_model``.

    Regression test for https://github.com/aiidateam/aiida-core/issues/7379: a plugin that does not support
    CLI-based creation (``supports_cli_model = False``, e.g. ``AbstractCode``) used to crash the group with an
    ``UnsupportedSchemaError``; it must now be dropped from the listing and resolve to a user-facing
    :class:`click.exceptions.UsageError`. A ``cli_exposed = False`` plugin, being capable, stays resolvable when
    invoked explicitly, it is only kept out of the listing.
    """
    entry_points.add(CustomClass, 'aiida.custom:custom')
    entry_points.add(NoCliModelCustomClass, 'aiida.custom:no_cli_model')
    entry_points.add(HiddenCustomClass, 'aiida.custom:hidden')
    group = DynamicEntryPointCommandGroup(lambda *args, **kwargs: True, name='create', entry_point_group='aiida.custom')

    ctx = click.Context(group)
    assert (cmd_name in group.list_commands(ctx)) is listed
    if resolvable:
        assert group.get_command(ctx, cmd_name) is not None
    else:
        with pytest.raises(click.exceptions.UsageError):
            group.get_command(ctx, cmd_name)

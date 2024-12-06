"""Tests for :mod:`aiida.cmdline.groups.dynamic`."""

import typing as t

from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from aiida.cmdline.groups.dynamic import DynamicEntryPointCommandGroup


class CustomClass:
    """Test plugin class."""

    class Model(BaseModel):
        """Model configuration."""

        optional_type: t.Union[int, float] = Field(title='Optional type')
        union_type: t.Union[int, float] = Field(title='Union type')
        without_default: str = Field(title='Without default')
        with_default: str = Field(title='With default', default='default')
        with_default_factory: str = Field(title='With default factory', default_factory=lambda: True)  # type: ignore[assignment]


def test_list_options(entry_points):
    """Test :meth:`aiida.cmdline.groups.dynamic.DyanmicEntryPointCommandGroup.list_options`."""
    entry_points.add(CustomClass, 'aiida.custom:custom')

    group = DynamicEntryPointCommandGroup(lambda *args, **kwargs: True, entry_point_group='aiida.custom')

    for option_decorators in group.list_options('custom'):
        option = option_decorators(lambda x: True).__click_params__[0]
        field = CustomClass.Model.model_fields[option.name]
        assert option.default == field.default_factory if field.default is PydanticUndefined else field.default
        assert option.type == t.get_args(field.annotation) or field.annotation

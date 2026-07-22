###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common CLI utilities for broker plugins."""

from __future__ import annotations

import functools
import typing as t
from collections.abc import Callable

import click

from aiida.brokers.broker import Broker
from aiida.cmdline.params import types
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.plugins import BrokerFactory

__all__ = ('configure_broker_options',)

ParamTypeFactory = Callable[[t.Any], click.ParamType | t.Any]

_PARAM_TYPES: dict[str, ParamTypeFactory] = {
    'bool': lambda _field: click.BOOL,
    'choice': lambda field: click.Choice(field.choices or ()),
    'non_empty_string': lambda _field: types.NonEmptyStringParamType(),
    'hostname': lambda _field: types.HostnameType(),
    'int': lambda _field: click.INT,
    'string': lambda _field: click.types.StringParamType(),
}


def _get_profile_config_default(ctx: click.Context, option_name: str, default: t.Any) -> t.Any:
    """Return the current profile value for a broker config option, if available."""
    profile = ctx.params.get('profile')

    if profile is None:
        return default

    try:
        return profile.dictionary['process_control']['config'][option_name]
    except (KeyError, TypeError):
        return default


def _get_detected_config(ctx: click.Context, broker_cls: type[Broker]) -> dict[str, t.Any]:
    """Return detected broker configuration for interactive defaults, cached on the click context."""
    cache_key = f'configure_broker_detected_config:{broker_cls.__module__}.{broker_cls.__name__}'

    if cache_key not in ctx.obj:
        try:
            ctx.obj[cache_key] = broker_cls.get_detected_config(lambda key: _get_profile_config_default(ctx, key, None))
        except ConnectionError:
            ctx.obj[cache_key] = {}

    return t.cast(dict[str, t.Any], ctx.obj[cache_key])


def _get_option_default(broker_cls: type[Broker], ctx: click.Context, option_name: str, default: t.Any) -> t.Any:
    """Return the interactive default for a broker configuration option."""
    detected_config = _get_detected_config(ctx, broker_cls)
    return detected_config.get(option_name, _get_profile_config_default(ctx, option_name, default))


def _get_param_type(field: t.Any) -> click.ParamType | t.Any:
    """Return the click parameter type for a broker configuration field."""
    try:
        factory = _PARAM_TYPES[field.param_type]
    except KeyError as exception:
        valid_kinds = ', '.join(sorted(_PARAM_TYPES))
        msg = f'unsupported broker config field param type `{field.param_type}`; valid kinds: {valid_kinds}'
        raise ValueError(msg) from exception

    return factory(field)


def configure_broker_options(
    entry_point_name: str,
) -> Callable[[Callable[..., t.Any]], Callable[..., t.Any]]:
    """Return a decorator that adds broker configuration options to a command."""
    broker_cls = BrokerFactory(entry_point_name)

    def apply_options(func: Callable[..., t.Any]) -> Callable[..., t.Any]:
        decorators = [
            click.option(
                f'--{field.name.replace("_", "-")}',
                required=True,
                prompt=field.prompt,
                help=field.help,
                default=field.default,
                show_default=not field.hide_input,
                type=_get_param_type(field),
                hide_input=field.hide_input,
                cls=InteractiveOption,
                contextual_default=functools.partial(
                    _get_option_default,
                    broker_cls,
                    option_name=field.name,
                    default=field.default,
                ),
            )
            for field in broker_cls._config_fields
            if field.expose_cli
        ]

        for decorator in reversed(decorators):
            func = decorator(func)

        return func

    return apply_options

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""".. py:module::config
    :synopsis: Convenience class for configuration file option

The functions :func:`configuration_callback` and :func:`configuration_option` were directly taken from the repository
https://github.com/phha/click_config_file/blob/7b93a20b4c79458987fac116418859f30a16d82a/click_config_file.py with a
minor modification to ``configuration_callback`` to add a check for unknown parameters in the configuration file and
the default provider is changed to :func:`yaml_config_file_provider`.
"""

from __future__ import annotations

import functools
import os
import typing as t

import click

from .overridable import OverridableOption

if t.TYPE_CHECKING:
    from click.decorators import FC

__all__ = ('ConfigFileOption',)


def yaml_config_file_provider(handle: t.Any, _cmd_name: t.Any) -> t.Any:
    """Read yaml config file from file handle."""
    import yaml

    return yaml.safe_load(handle)


def configuration_callback(
    cmd_name: str | None,
    option_name: str,
    config_file_name: str,
    saved_callback: t.Callable[..., t.Any] | None,
    provider: t.Callable[..., t.Any],
    implicit: bool,
    ctx: click.Context,
    param: click.Parameter,
    value: t.Any,
) -> t.Any:
    """Callback for reading the config file.

    Also takes care of calling user specified custom callback afterwards.

    :param cmd_name: The command name. This is used to determine the configuration directory.
    :param option_name: The name of the option. This is used for error messages.
    :param config_file_name: The name of the configuration file.
    :param saved_callback: User-specified callback to be called later.
    :param provider: A callable that parses the configuration file and returns a dictionary of the configuration
        parameters. Will be called as ``provider(file_path, cmd_name)``. Default: ``yaml_config_file_provider``.
    :param implicit: Whether a implicit value should be applied if no configuration option value was provided.
    :param ctx: ``click`` context.
    :param param: ``click`` parameters.
    :param value: Value passed to the parameter.
    """
    ctx.default_map = ctx.default_map or {}
    cmd_name = cmd_name or ctx.info_name

    if implicit:
        default_value = os.path.join(click.get_app_dir(cmd_name), config_file_name)  # type: ignore[arg-type]
        param.default = default_value
        value = value or default_value

    if value:
        try:
            config = provider(value, cmd_name)
        except Exception as exception:
            raise click.BadOptionUsage(option_name, f'Error reading configuration file: {exception}', ctx)

        valid_params = [param.name for param in ctx.command.params if param.name != option_name]
        specified_params = list(config.keys())
        unknown_params = set(specified_params).difference(set(valid_params))

        if unknown_params:
            raise click.BadParameter(
                f'Invalid configuration file, the following keys are not supported: {unknown_params}', ctx, param
            )

        ctx.default_map.update(config)

    return saved_callback(ctx, param, value) if saved_callback else value


def configuration_option(*param_decls: t.Any, **attrs: t.Any) -> t.Callable[[FC], FC]:
    """Adds configuration file support to a click application.

    This will create an option of type ``click.File`` expecting the path to a configuration file. When specified, it
    overwrites the default values for all other click arguments or options with the corresponding value from the
    configuration file. The default name of the option is ``--config``. By default, the configuration will be read from
    a configuration directory as determined by ``click.get_app_dir``. This decorator accepts the same arguments as
    ``click.option`` and ``click.Path``. In addition, the following keyword arguments are available:

    :param cmd_name: str
        The command name. This is used to determine the configuration directory. Default: ``ctx.info_name``.
    :param config_file_name: str
        The name of the configuration file. Default: ``config``.
    :param implicit: bool
        If ``True`` then implicitly create a value for the configuration option using the above parameters. If a
        configuration file exists in this path it will be applied even if no configuration option was suppplied as a
        CLI argument or environment variable. If ``False`` only apply a configuration file that has been explicitely
        specified. Default: ``False``.
    :param provider: callable
        A callable that parses the configuration file and returns a dictionary of the configuration parameters. Will be
        called as ``provider(file_path, cmd_name)``. Default: ``yaml_config_file_provider``.
    """
    param_decls = param_decls or ('--config',)
    option_name = param_decls[0]

    def decorator(func: FC) -> FC:
        attrs.setdefault('is_eager', True)
        attrs.setdefault('help', 'Read configuration from FILE.')
        attrs.setdefault('expose_value', False)
        implicit = attrs.pop('implicit', True)
        cmd_name = attrs.pop('cmd_name', None)
        config_file_name = attrs.pop('config_file_name', 'config')
        provider = attrs.pop('provider', yaml_config_file_provider)
        path_default_params = {
            'exists': False,
            'file_okay': True,
            'dir_okay': False,
            'writable': False,
            'readable': True,
            'resolve_path': False,
        }
        path_params = {k: attrs.pop(k, v) for k, v in path_default_params.items()}
        attrs['type'] = attrs.get('type', click.Path(**path_params))
        saved_callback = attrs.pop('callback', None)
        partial_callback = functools.partial(
            configuration_callback, cmd_name, option_name, config_file_name, saved_callback, provider, implicit
        )
        attrs['callback'] = partial_callback
        return click.option(*param_decls, **attrs)(func)

    return decorator


class ConfigFileOption(OverridableOption):
    """Reusable option that reads a configuration file containing values for other command parameters.

    Example::

        CONFIG_FILE = ConfigFileOption('--config', help='A configuration file')

        @click.command()
        @click.option('computer_name')
        @CONFIG_FILE(help='Configuration file for computer_setup')
        def computer_setup(computer_name):
            click.echo(f"Setting up computer {computername}")

        computer_setup --config config.yml

    with config.yml::

        ---
        computer_name: computer1

    """

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        """Store the default args and kwargs.

        :param args: default arguments to be used for the option
        :param kwargs: default keyword arguments to be used that can be overridden in the call
        """
        kwargs.update({'provider': yaml_config_file_provider, 'implicit': False})
        super().__init__(*args, **kwargs)

    def __call__(self, **kwargs: t.Any) -> t.Any:
        """Override the stored kwargs, (ignoring args as we do not allow option name changes) and return the option.

        :param kwargs: keyword arguments that will override those set in the construction
        :return: click_config_file.configuration_option constructed with args and kwargs defined during construction
            and call of this instance
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)

        return configuration_option(*self.args, **kw_copy)

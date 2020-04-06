# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Option for setting global verbosity of verdi command line interface."""

import click
from aiida.common.log import VERDI_LOGGER, LOG_LEVELS
from aiida.manage.configuration import get_config_option
from .overridable import OverridableOption


class VerbosityOption(OverridableOption):
    """
    Option for controlling verbosity of loggers (default: "verdi" logger).

    Example::

        VERBOSITY = VerbosityOption('-v', '--verbosity', logger=MY_LOGGER)

        @click.command()
        @VERBOSITY()
        def computer_setup(computer_name):
            click.echo("Setting up computer {}".format(computername))

        computer_setup -v DEBUG

    """

    def __init__(self, *args, **kwargs):
        """
        Store the default args and kwargs.

        :param args: default arguments to be used for the option
        :param kwargs: default keyword arguments to be used that can be overridden in the call
        """
        levels_str = ', '.join(LOG_LEVELS.keys())
        self.logger = kwargs.pop('logger', VERDI_LOGGER)

        kwargs.setdefault('default', get_config_option('logging.verdi_loglevel'))
        kwargs.setdefault('show_default', True)
        kwargs.setdefault('expose_value', False)
        kwargs.setdefault(
            'help', 'Control the verbosity of messages emitted by the command' +
            ' by setting the minimum log level to one of: {}.'.format(levels_str)
        )
        kwargs.setdefault('is_eager', True)
        kwargs.setdefault('callback', self._set_level)

        super().__init__(*args, **kwargs)

    def __call__(self, **kwargs):
        """
        Override the stored kwargs, (ignoring args as we do not allow option name changes) and return the option.

        :param kwargs: keyword arguments that will override those set in the construction
        :return: click_config_file.configuration_option constructed with args and kwargs defined during construction
            and call of this instance
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)

        if 'logger' in kw_copy:
            self.logger = kw_copy.get('logger')

        return click.option(*self.args, **kw_copy)

    def _set_level(self, ctx, param, value):  # pylint: disable=unused-argument
        """Set level of relevant logger."""
        level = LOG_LEVELS.get(value.upper(), None)
        if level is None:
            levels_str = ', '.join(LOG_LEVELS.keys())
            raise click.BadParameter('Must be one of {}.'.format(levels_str))
        self.logger.setLevel(level)

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to operate on styling of standard outputs."""

import os
from typing import Optional, Union


# Defines the styling for the process states
class ProcessStateStyle:
    COLOR_CREATED_RUNNING = 'blue'
    COLOR_WAITING = 'yellow'
    COLOR_FINISHED = 'green'
    COLOR_KILLED_EXPECTED = 'red'

    SYMBOL_EXPECTED = '\u2a2f'
    SYMBOL_KILLED = '\u2620'
    SYMBOL_CREATED_FINISHED = '\u23f9'
    SYMBOL_RUNNING_WAITING = '\u23f5'
    SYMBOL_RUNNING_WAITING_PAUSED = '\u23f8'


class ColorConfig:
    """Controls the color styling option for aiida command outputs."""

    _COLOR: Union[bool, None] = None

    @staticmethod
    def get_color() -> Union[bool, None]:
        """
        Returns the color value. If return value is None, the color value should be determined by caller.
        """
        return ColorConfig._COLOR

    @staticmethod
    def set_color(cli_color_option: Optional[bool] = None):
        """
        Sets the color value that is determined from the CLI option or, if not
        given, by the environment variables `FORCE_COLOR` and `NO_COLOR`. If also
        no environment variable is given it set to `None` which signifies that
        the caller of :meth:`~aiida.common.style.get_color` should determine if
        output should allow colors.

        The logic for `FORCE_COLOR` and `NO_COLOR` follows the Python 3.13 implementation
        See https://docs.python.org/3.13/using/cmdline.html#using-on-controlling-color

        :param cli_color_option: The option given over the CLI.
        """
        ColorConfig._COLOR = None

        if cli_color_option is not None:
            ColorConfig._COLOR = cli_color_option
        else:
            # Determines color for the terminal output depending on NO_COLOR and FORCE_COLOR
            # environment variables following the Python implementation.
            # See https://docs.python.org/3.13/using/cmdline.html#using-on-controlling-color
            if os.getenv('TERM') == 'dump':
                ColorConfig._COLOR = False
            if 'FORCE_COLOR' in os.environ:
                ColorConfig._COLOR = True
            if 'NO_COLOR' in os.environ:
                ColorConfig._COLOR = False

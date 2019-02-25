# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module to define multi value options for click.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from .. import types


class MultipleValueOption(click.Option):
    """
    An option that can handle multiple values with a single flag. For example::

        @click.option('-n', '--nodes', cls=MultipleValueOption)

    Will be able to parse the following::

        --nodes 10 15 12

    This is better than the builtin ``multiple=True`` keyword for click's option which forces the user to specify
    the option flag for each value, which gets impractical for long lists of values
    """

    def __init__(self, *args, **kwargs):
        param_type = kwargs.pop('type', None)

        if param_type is not None:
            kwargs['type'] = types.MultipleValueParamType(param_type)

        super(MultipleValueOption, self).__init__(*args, **kwargs)
        self._previous_parser_process = None
        self._eat_all_parser = None

    def add_to_parser(self, parser, ctx):
        """
        Override built in click method that allows us to specify a custom parser
        to eat up parameters until the following flag or 'endopt' (i.e. --)
        """
        # pylint: disable=protected-access

        result = super(MultipleValueOption, self).add_to_parser(parser, ctx)

        def parser_process(value, state):
            """
            The actual function that parses the options

            :param value: The value to parse
            :param state: The state of the parser
            """
            # pylint: disable=invalid-name
            ENDOPTS = '--'
            done = False
            value = [value]

            # Grab everything up to the next option or endopts symbol
            while state.rargs and not done:
                for prefix in self._eat_all_parser.prefixes:
                    if state.rargs[0].startswith(prefix) or state.rargs[0] == ENDOPTS:
                        done = True
                if not done:
                    value.append(state.rargs.pop(0))

            value = tuple(value)

            self._previous_parser_process(value, state)

        for name in self.opts:
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break

        return result

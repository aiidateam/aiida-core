###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define multi value options for click."""

import typing as t

import click

from .. import types

__all__ = ('MultipleValueOption',)


def collect_usage_pieces(self: click.Command, ctx: click.Context) -> list[str]:
    """Returns all the pieces that go into the usage line and returns it as a list of strings."""
    result = [self.options_metavar]

    # If the command contains a `MultipleValueOption` make sure to add `[--]` to the help string before the
    # arguments, which hints the use of the optional `endopts` marker
    if any(isinstance(param, MultipleValueOption) for param in self.get_params(ctx)):
        result.append('[--]')

    for param in self.get_params(ctx):
        result.extend(param.get_usage_pieces(ctx))

    return result  # type: ignore[return-value]


# Override the `collect_usage_pieces` method of the `click.Command` class to automatically affect all commands
click.Command.collect_usage_pieces = collect_usage_pieces  # type: ignore[method-assign]


class MultipleValueOption(click.Option):
    """An option that can handle multiple values with a single flag. For example::

        @click.option('-n', '--nodes', cls=MultipleValueOption)

    Will be able to parse the following::

        --nodes 10 15 12

    This is better than the builtin ``multiple=True`` keyword for click's option which forces the user to specify
    the option flag for each value, which gets impractical for long lists of values
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        param_type = kwargs.pop('type', None)

        if param_type is not None:
            kwargs['type'] = types.MultipleValueParamType(param_type)

        super().__init__(*args, **kwargs)
        self._previous_parser_process: t.Callable[[t.Any, click.parser.ParsingState], None] | None = None
        self._eat_all_parser: click.parser.Option | None = None

    # TODO: add_to_parser has been deprecated in 8.2.0
    def add_to_parser(self, parser: click.parser.OptionParser, ctx: click.Context) -> None:
        """Override built in click method that allows us to specify a custom parser
        to eat up parameters until the following flag or 'endopt' (i.e. --)
        """
        super().add_to_parser(parser, ctx)

        def parser_process(value: t.Any, state: click.parser.ParsingState) -> None:
            """The actual function that parses the options

            :param value: The value to parse
            :param state: The state of the parser
            """
            ENDOPTS = '--'  # noqa: N806
            done = False
            value = [value]

            # Grab everything up to the next option or endopts symbol
            while state.rargs and not done:
                for prefix in self._eat_all_parser.prefixes:  # type: ignore[union-attr]
                    if state.rargs[0].startswith(prefix) or state.rargs[0] == ENDOPTS:
                        done = True
                if not done:
                    value.append(state.rargs.pop(0))

            value = tuple(value)

            self._previous_parser_process(value, state)  # type: ignore[misc]

        for name in self.opts:
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process  # type: ignore[method-assign]
                break

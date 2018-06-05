import click

from aiida.cmdline.params import types


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
        result = super(MultipleValueOption, self).add_to_parser(parser, ctx)

        def parser_process(value, state):
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

# -*- coding: utf-8 -*-
from __future__ import absolute_import 
import click
from . import validators


class MultipleValueParamType(click.ParamType):

    def __init__(self, param_type):
        super(MultipleValueParamType, self).__init__()
        self._param_type = param_type
        self.name = param_type.__name__.upper()

    def convert(self, value, param, ctx):
        try:
            return tuple([self._param_type(entry) for entry in value])
        except ValueError:
            self.fail('could not convert {} into type {}'.format(value, self._param_type))


class MultipleValueOption(click.Option):
    """
    An option that can handle multiple values with a single flag. For example::

        @click.option('-n', '--nodes', cls=MultipleValueOption)

    Will be able to parse the following::

        --nodes 10 15 12

    This is better than the builtin ``multiple=True`` keyword for click's option which forces the user to specify
    the option flag for each value, which gets inpractical for long lists of values
    """

    def __init__(self, *args, **kwargs):
        param_type = kwargs.pop('type', None)

        if param_type is not None:
            kwargs['type'] = MultipleValueParamType(param_type)

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


class overridable_option(object):
    """
    Wrapper around click option that allows to store the name
    and some defaults but also to override them later, for example
    to change the help message for a certain command.
    """

    def __init__(self, *args, **kwargs):
        """
        Store the defaults
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """
        Override args if passed and update the kwargs and return the click.option
        If a callback is specified in the kwargs make sure to bind the callback_kwargs
        to it using the partial lambda construct of functools
        """
        import functools

        if not args:
            args_copy = self.args
        else:
            args_copy = args

        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)

        # Pop the optional callback_kwargs if present
        callback_kwargs = kw_copy.pop('callback_kwargs', {})

        if 'callback' in kw_copy:
            callback_plain = kw_copy['callback']
            callback_bound = functools.partial(callback_plain, callback_kwargs)
            kw_copy['callback'] = callback_bound

        return click.option(*args_copy, **kw_copy)


code = overridable_option(
    '-c', '--code', type=click.STRING, required=True,
    callback=validators.validate_code,
    help='the label of the AiiDA code object to use'
)


structure = overridable_option(
    '-s', '--structure', type=click.INT, required=True,
    callback=validators.validate_structure,
    help='the pk of a structure node'
)


pseudo_family = overridable_option(
    '-p', '--pseudo-family', type=click.STRING, required=True,
    callback=validators.validate_pseudo_family,
    help='the name of the pseudo potential family to use'
)


kpoint_mesh = overridable_option(
    '-k', '--kpoint-mesh', 'kpoints', nargs=3, type=click.INT, default=[2, 2, 2], show_default=True,
    callback=validators.validate_kpoint_mesh,
    help='the number of points in the kpoint mesh along each basis vector'
)


calculation = overridable_option(
    '-C', '--calculation', type=click.INT, required=True,
    callback=validators.validate_calculation,
    help='the pk of a calculation node'
)


max_num_machines = overridable_option(
    '-m', '--max-num-machines', type=click.INT, default=1, show_default=True,
    help='the maximum number of machines (nodes) to use for the calculations'
)


max_wallclock_seconds = overridable_option(
    '-w', '--max-wallclock-seconds', type=click.INT, default=1800, show_default=True,
    help='the maximum wallclock time in seconds to set for the calculations'
)


daemon = overridable_option(
    '-d', '--daemon', is_flag=True, default=False, show_default=True,
    help='submit the workchain to the daemon instead of running it locally'
)


group = overridable_option(
    '-g', '--group', type=click.STRING, required=True,
    callback=validators.validate_group,
    help='the name or pk of a Group'
)
# -*- coding: utf-8 -*-
# yapf: disable
import click

from . import types


class OverridableOption(object):
    """
    Wrapper around click option that increases reusability

    Click options are reusable already but sometimes it can improve the user interface to for example customize a
    help message for an option on a per-command basis. Sometimes the option should be prompted for if it is not given
    On some commands an option might take any folder path, while on another the path only has to exist.

    Overridable options store the arguments to click.option and only instanciate the click.Option on call,
    kwargs given to ``__call__`` override the stored ones.

    Example::

        FOLDER = OverridableOption('--folder', type=click.Path(file_okay=False), help='A folder')

        @click.command()
        @FOLDER(help='A folder, will be created if it does not exist')
        def ls_or_create(folder):
            click.echo(os.listdir(folder))

        @click.command()
        @FOLDER(help='An existing folder', type=click.Path(exists=True, file_okay=False, readable=True)
        def ls(folder)
            click.echo(os.listdir(folder))
    """

    def __init__(self, *args, **kwargs):
        """
        Store the default args and kwargs
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, **kwargs):
        """
        Override the stored kwargs, (ignoring args as we do not allow option name changes) and return the option
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        return click.option(*self.args, **kw_copy)


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


CALCULATION = OverridableOption('-C', '--calculation', 'calculation', type=types.CalculationParamType(),
    help='a single calculation identified by its ID or UUID')


CALCULATIONS = OverridableOption('-C', '--calculations', 'calculations', cls=MultipleValueOption, type=types.CalculationParamType(),
    help='one or multiple calculations identified by their ID or UUID')


CODE = OverridableOption('-X', '--code', 'code', type=types.CodeParamType(),
    help='a single code identified by its ID, UUID or label')


CODES = OverridableOption('-X', '--codes', 'codes', cls=MultipleValueOption, type=types.CodeParamType(),
    help='one or multiple codes identified by their ID, UUID or label')


COMPUTER = OverridableOption('-Y', '--computer', 'computer', type=types.ComputerParamType(),
    help='a single computer identified by its ID, UUID or label')


COMPUTERS = OverridableOption('-Y', '--computers', 'computers', cls=MultipleValueOption, type=types.ComputerParamType(),
    help='one or multiple computers identified by their ID, UUID or label')


DATUM = OverridableOption('-D', '--datum', 'datum', type=types.DataParamType(),
    help='a single datum identified by its ID, UUID or label')


DATA = OverridableOption('-D', '--data', 'data', cls=MultipleValueOption, type=types.DataParamType(),
    help='one or multiple data identified by their ID, UUID or label')


GROUP = OverridableOption('-G', '--group', 'group', type=types.GroupParamType(),
    help='a single group identified by its ID, UUID or name')


GROUPS = OverridableOption('-G', '--groups', 'groups', cls=MultipleValueOption, type=types.GroupParamType(),
    help='one or multiple groups identified by their ID, UUID or name')


NODE = OverridableOption('-N', '--node', 'node', type=types.NodeParamType(),
    help='a single node identified by its ID or UUID')


NODES = OverridableOption('-N', '--nodes', 'nodes', cls=MultipleValueOption, type=types.NodeParamType(),
    help='one or multiple nodes identified by their ID or UUID')


FORCE = OverridableOption('-f', '--force', is_flag=True, default=False,
    help='do not ask for confirmation')


SILENT = OverridableOption('-s', '--silent', is_flag=True, default=False,
    help='suppres any output printed to stdout')


ARCHIVE_FORMAT = OverridableOption('-F', '--archive-format', type=click.Choice(['zip', 'zip-uncompressed', 'tar.gz']),
    help='the format of the archive file', default='zip', show_default=True)


CALCULATION = OverridableOption('-C', '--calculation', 'calculation', type=types.CalculationParamType(),
    help='A single calculation identified by its ID or UUID')


CALCULATIONS = OverridableOption('-C', '--calculations', 'calculations', cls=MultipleValueOption, type=types.CalculationParamType(),
    help='One or multiple calculations identified by their ID or UUID')

NON_INTERACTIVE = OverridableOption('-n', '--non-interactive', is_flag=True, is_eager=True,
    help='Noninteractive mode: never prompt the user for input')

PREPEND_TEXT = OverridableOption('--prepend-text', type=str, default='',
    help='Bash script to be executed before an action')

APPEND_TEXT = OverridableOption('--append-text', type=str, default='',
    help='Bash script to be executed after an action has completed')

LABEL = OverridableOption('-L', '--label', help='short text to be used as a label')
DESCRIPTION = OverridableOption('-D', '--description', help='(text) description')

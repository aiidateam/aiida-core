###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience class which can be used to defined a set of commonly used options that can be easily reused."""

import typing as t

import click

__all__ = ('OverridableOption',)


class OverridableOption:
    """Wrapper around click option that increases reusability

    Click options are reusable already but sometimes it can improve the user interface to for example customize a
    help message for an option on a per-command basis. Sometimes the option should be prompted for if it is not given
    On some commands an option might take any folder path, while on another the path only has to exist.

    Overridable options store the arguments to click.option and only instantiate the click.Option on call,
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

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        """Store the default args and kwargs.

        :param args: default arguments to be used for the click option
        :param kwargs: default keyword arguments to be used that can be overridden in the call
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, **kwargs: t.Any) -> t.Callable[[t.Any], t.Any]:
        """Override the stored kwargs, (ignoring args as we do not allow option name changes) and return the option.

        :param kwargs: keyword arguments that will override those set in the construction
        :return: click option constructed with args and kwargs defined during construction and call of this instance
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        return click.option(*self.args, **kw_copy)

    def clone(self, **kwargs: t.Any) -> 'OverridableOption':
        """Create a new instance of by cloning the current instance and updating the stored kwargs with those passed.

        This can be useful when an already predefined OverridableOption needs to be further specified and reused
        by a set of sub commands. Example::

            LABEL = OverridableOption('-l', '--label', required=False, help='The label of the node'
            LABEL_COMPUTER = LABEL.clone(required=True, help='The label of the computer')

        If multiple computer related sub commands need the LABEL option, but the default help string and required
        attribute need to be different, the `clone` method allows to override these and create a new OverridableOption
        instance that can then be used as a decorator.

        :param kwargs: keyword arguments to update
        :return: OverridableOption instance with stored keyword arguments updated
        """
        import copy

        clone = copy.deepcopy(self)
        clone.kwargs.update(kwargs)
        return clone

#-*- coding: utf8 -*-
"""
.. py:module::overridable
    :synopsis: Convenience class which can be used to defined a set of commonly used options that
        can be easily reused and which improves consistency across the command line interface
"""
import click


class OverridableOption(object):
    """
    Wrapper around click option that increases reusability

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

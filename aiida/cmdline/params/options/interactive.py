# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
.. module::interactive
    :synopsis: Tools and an option class for interactive parameter entry with
    additional features such as help lookup.
"""
import click

from aiida.cmdline.utils import echo
from .conditional import ConditionalOption


class InteractiveOption(ConditionalOption):
    """
    Prompts for input, intercepting certain keyword arguments to replace :mod:`click`'s prompting
    behaviour with a more feature-rich one.

    .. note:: This class has a parameter ``required_fn`` that can be passed to its ``__init__`` (inherited
        from the superclass :py:class:`~aiida.cmdline.params.options.conditional.ConditionalOption`) and a
        ``prompt_fn``.

        - ``required_fn`` is about "is this parameter required" depending on the value of other params.
        - ``prompt_fn`` is about "should I prompt for this value if in interactive mode" and only makes sense
          in this class and not in :py:class:`~aiida.cmdline.params.options.conditional.ConditionalOption`.

        In most usecases, if I have a ``prompt_fn``, then I would like to have also (the same) ``required_fn``.
        The implementation still makes them independent for usecases where they might be different functions
        (e.g. if the variable is anyway not required, but you want to decide whether to prompt for it or not).

    Usage::

        import click

        @click.command()
        @click.option('label', prompt='Label', cls=InteractiveOption)
        def foo(label):
            click.echo(f'Labeling with label: {label}')
    """

    PROMPT_COLOR = 'yellow'
    CHARACTER_PROMPT_HELP = '?'
    CHARACTER_IGNORE_DEFAULT = '!'

    def __init__(self, param_decls=None, switch=None, prompt_fn=None, contextual_default=None, **kwargs):
        """
        :param param_decls: relayed to :class:`click.Option`
        :param switch: sequence of parameter
        :param prompt_fn: callable(ctx) -> True | False, returns True
            if the option should be prompted for in interactive mode.
        :param contextual_default: An optional callback function to get a default which is
            passed the click context

        """
        # intercept prompt kwarg; I need to pop it before calling super
        self._prompt = kwargs.pop('prompt', None)

        # call super class here, after removing `prompt` from the kwargs.
        super().__init__(param_decls=param_decls, **kwargs)

        self.prompt_fn = prompt_fn

        # I check that a prompt was actually defined.
        # I do it after calling super so e.g. 'self.name' is defined
        if not self._prompt:
            raise TypeError(
                f"Interactive options need to have a prompt specified, but '{self.name}' does not have a prompt defined"
            )

        # other kwargs
        self.switch = switch
        self._contextual_default = contextual_default

        # set callback
        self._after_callback = self.callback
        self.callback = self.prompt_callback

        # set control strings that trigger special features from the input prompt
        self._ctrl = {'?': self.ctrl_help}

        # set prompting type
        self.prompt_loop = self.simple_prompt_loop

    @staticmethod
    def is_non_interactive(ctx):
        """Return whether the command is being run non-interactively.

        This is the case if the `non_interactive` parameter in the context is set to `True`.

        :return: boolean, True if being run non-interactively, False otherwise
        """
        return ctx.params.get('non_interactive')

    def get_default(self, ctx):
        """disable :mod:`click` from circumventing prompting when a default value exists"""
        return None

    def _get_default(self, ctx):
        """provides the functionality of :meth:`click.Option.get_default`"""
        if self._contextual_default is not None:
            default = self._contextual_default(ctx)
        else:
            default = super().get_default(ctx)

        try:
            default = self.type.deconvert_default(default)
        except AttributeError:
            pass

        return default

    @staticmethod
    def custom_value_proc(value):
        """Custom value_proc function for the click.prompt which it will call to do value conversion.

        Simply return the value, because we want to take care of value conversion ourselves in the `simple_prompt_loop`.
        If we let `click.prompt` do it, it will raise an exception when the user passes a control character, like the
        question mark, to bring up the help message and the type of the option is not a string, causing conversion to
        fail.
        """
        return value

    def prompt_func(self, ctx):
        """prompt function with args set"""
        return click.prompt(
            click.style(self._prompt, fg=self.PROMPT_COLOR),
            type=self.type,
            value_proc=self.custom_value_proc,
            prompt_suffix=click.style(': ', fg=self.PROMPT_COLOR),
            default=self._get_default(ctx),
            hide_input=self.hide_input,
            confirmation_prompt=self.confirmation_prompt
        )

    def ctrl_help(self):
        """control behaviour when help is requested from the prompt"""
        echo.echo_info(self.format_help_message())

    def format_help_message(self):
        """
        format the message to be displayed for in-prompt help.

        gives a list of possibilities for parameter types that support completion
        """
        msg = self.help or f'Expecting {self.type.name}'
        choices = getattr(self.type, 'complete', lambda x, y: [])(None, '')
        if choices:
            choice_table = []
            msg += '\nSelect one of:\n'
            for choice in choices:
                if isinstance(choice, tuple):
                    choice_table.append('\t{:<12} {}'.format(*choice))
                else:
                    choice_table.append(f'\t{choice:<12}')
            msg += '\n'.join(choice_table)
        return msg

    def full_process_value(self, ctx, value):
        """
        catch errors raised by ConditionalOption in order to adress them in
        the callback
        """
        try:
            value = super().full_process_value(ctx, value)
        except click.MissingParameter:
            pass
        return value

    def safely_convert(self, value, param, ctx):
        """
        convert without raising, instead print a message if fails

        :return: Tuple of ( success (bool), converted value )
        """
        successful = False

        if value is self.CHARACTER_IGNORE_DEFAULT:
            # The ignore default character signifies that the user wants to "not" set the value.
            # Replace value by an empty string for further processing (e.g. if a non-empty value is required).
            value = ''

        try:
            value = self.type.convert(value, param, ctx)
            value = self.callback(ctx, param, value)
            successful = True
        except click.BadParameter as err:
            echo.echo_error(str(err))
            self.ctrl_help()

        return successful, value

    def simple_prompt_loop(self, ctx, param, value):
        """Prompt until successful conversion. dispatch control sequences."""
        if not hasattr(ctx, 'prompt_loop_info_printed'):
            echo.echo_info(f'enter "{self.CHARACTER_PROMPT_HELP}" for help')
            echo.echo_info(f'enter "{self.CHARACTER_IGNORE_DEFAULT}" to ignore the default and set no value')
            ctx.prompt_loop_info_printed = True

        while 1:
            # prompt
            value = self.prompt_func(ctx)
            if value in self._ctrl:
                # dispatch - e.g. show help
                self._ctrl[value]()
                continue

            # try to convert, if unsuccessful continue prompting
            successful, value = self.safely_convert(value, param, ctx)
            if successful:
                return value

    def after_callback(self, ctx, param, value):
        """If a callback was registered on init, call it and return it's value."""
        if self._after_callback:
            try:
                self._after_callback(ctx, param, value)
            except click.BadParameter as exception:
                # If the non-prompt callback raises, we want to only start the prompt loop if we were already in it.
                # For example, if the option was explicitly specified on the command line, but the callback fails, we
                # do not want to start prompting for it, but instead just let the exception bubble-up.
                # However, in this case, the `--non-interactive` flag is not necessarily passed, so we cannot just rely
                # on this value but in addition need to check that we did not already enter the prompt.
                if self.is_non_interactive(ctx) or not hasattr(ctx, 'prompt_loop_info_printed'):
                    raise exception

                echo.echo_error(str(exception))
                self.ctrl_help()
                value = self.prompt_loop(ctx, param, value)

        return value

    def prompt_callback(self, ctx, param, value):
        """decide wether to initiate the prompt_loop or not"""

        # From click.core.Context:
        # if resilient_parsing is enabled then Click will parse without any interactivity or callback invocation.
        # Therefore if this flag is set, we should not do any prompting.
        if ctx.resilient_parsing:
            return None

        # a value was given on the command line: then just go with validation
        if value is not None:
            return self.after_callback(ctx, param, value)

        # The same if the user specified --non-interactive
        if self.is_non_interactive(ctx):

            # Check if it is required
            default = self._get_default(ctx) or self.default

            if default is not None:
                # There is a default
                value = self.type.convert(default, param, ctx)
            else:
                # There is no default.
                # If required
                if self.is_required(ctx):
                    raise click.MissingParameter()
                # In the else case: no default, not required: value is None, it's just  passed to the after_callback
            return self.after_callback(ctx, param, value)

        if self.prompt_fn is None or (self.prompt_fn is not None and self.prompt_fn(ctx)):
            # There is no prompt_fn function, or a prompt_fn function and it says we should ask for the value

            # If we are here, we are in interactive mode and the parameter is not specified
            # We enter the prompt loop
            return self.prompt_loop(ctx, param, value)

        # There is a prompt_fn function and returns False (i.e. should not ask for this value
        # We then set the value to None
        value = None

        # And then we call the callback
        return self.after_callback(ctx, param, value)


class TemplateInteractiveOption(InteractiveOption):
    """Sub class of ``InteractiveOption`` that uses template file for input instead of simple inline prompt.

    This is useful for options that need to be able to specify multiline string values.
    """

    def __init__(self, param_decls=None, **kwargs):
        """Define the configuration for the multiline template in the keyword arguments.

        :param template: name of the template to use from the ``aiida.cmdline.templates`` directory.
            Default is the 'multiline.tpl' template.
        :param header: string to put in the header of the template.
        :param footer: string to put in the footer of the template.
        :param extension: file extension to give to the template file.
        """
        self.template = kwargs.pop('template', 'multiline.tpl')
        self.header = kwargs.pop('header', '')
        self.footer = kwargs.pop('footer', '')
        self.extension = kwargs.pop('extension', '')
        super().__init__(param_decls=param_decls, **kwargs)

    def prompt_func(self, ctx):
        """Replace the basic prompt with a method that opens a template file in an editor."""
        from aiida.cmdline.utils.multi_line_input import edit_multiline_template
        kwargs = {'value': self._get_default(ctx) or '', 'header': self.header, 'footer': self.footer}
        return edit_multiline_template(self.template, extension=self.extension, **kwargs)


def opt_prompter(ctx, cmd, givenkwargs, oldvalues=None):
    """
    Prompt interactively for the value of an option of the command with context ``ctx``.

    Used to produce more complex behaviours than can be achieved with InteractiveOption alone.
    """
    if not oldvalues:
        oldvalues = {}
    cmdparams = {i.name: i for i in cmd.params}

    def opt_prompt(opt, prompt, default=None):
        """Prompt interactively for the value of option ``opt``"""
        if not givenkwargs[opt]:
            optobj = cmdparams[opt]
            optobj._prompt = prompt  # pylint: disable=protected-access
            optobj.default = default or oldvalues.get(opt)
            return optobj.prompt_loop(ctx, optobj, givenkwargs[opt])
        return givenkwargs[opt]

    return opt_prompt

###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tools and an option class for interactive parameter entry with additional features such as help lookup."""

from __future__ import annotations

import typing as t

import click
from click.shell_completion import CompletionItem

from aiida.cmdline.utils import echo

from .conditional import ConditionalOption

if t.TYPE_CHECKING:
    from collections.abc import Sequence


class InteractiveOption(ConditionalOption):
    """Prompts for input, intercepting certain keyword arguments to provide more feature-rich behavior.

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

    PROMPT_COLOR = echo.COLORS['warning']
    CHARACTER_PROMPT_HELP = '?'
    CHARACTER_IGNORE_DEFAULT = '!'

    def __init__(
        self,
        param_decls: Sequence[str] | None = None,
        prompt_fn: t.Callable[[click.Context], bool] | None = None,
        contextual_default: t.Any | None = None,
        **kwargs: t.Any,
    ):
        """Construct a new instance.

        :param param_decls: relayed to :class:`click.Option`
        :param prompt_fn: callable(ctx) -> Bool, returns True if the option should be prompted for in interactive mode.
        :param contextual_default: An optional callback function to get a default which is passed the click context.
        """
        super().__init__(param_decls=param_decls, **kwargs)
        self._prompt_fn = prompt_fn
        self._contextual_default = contextual_default

    @property
    def prompt(self) -> str | None:
        """Return a colorized version of the prompt text."""
        return click.style(self._prompt, fg=self.PROMPT_COLOR)

    @prompt.setter
    def prompt(self, value: str | None) -> None:
        """Set the prompt text."""
        self._prompt = value

    def prompt_for_value(self, ctx: click.Context) -> t.Any:
        """Prompt for a value printing a generic help message if this is the first invocation of the command.

        If the command is invoked in non-interactive mode, meaning one should never prompt for a value, the default is
        returned instead of prompting.

        If the help message is printed, the ``prompt_loop_info_printed`` variable is set in the context which is used
        to check whether the message has already been printed as to only print it once at the first prompt.
        """
        if not self.is_interactive(ctx):
            return self.get_default(ctx)

        if self._prompt_fn is not None and self._prompt_fn(ctx) is False:
            return None

        if not hasattr(ctx, 'prompt_loop_info_printed'):
            echo.echo_report(f'enter {self.CHARACTER_PROMPT_HELP} for help.')
            echo.echo_report(f'enter {self.CHARACTER_IGNORE_DEFAULT} to ignore the default and set no value.')
            ctx.prompt_loop_info_printed = True  # type: ignore[attr-defined]

        return super().prompt_for_value(ctx)

    def process_value(self, ctx: click.Context, value: t.Any) -> t.Any:
        """Intercept any special characters before calling parent class if in interactive mode.

            * If the value matches ``CHARACTER_PROMPT_HELP``, echo ``get_help_message`` and reprompt.
            * If the value matches ``CHARACTER_IGNORE_DEFAULT``, ignore the value and return ``None``.

        Note that this logic only applies if the value is specified at the prompt, if it is provided from the command
        line, the value is actually taken as the value and processed as normal. To determine how the parameter was
        specified the ``click.Context.get_parameter_source`` method is used. The ``click.Parameter.handle_parse_result``
        method will set this after ``Parameter.consume_value``` is called but before ``Parameter.process_value`` is.
        """
        if self.name is None:
            return value

        source = ctx.get_parameter_source(self.name)

        if source is None:
            return value

        if value == self.CHARACTER_PROMPT_HELP and source is click.core.ParameterSource.PROMPT:
            click.echo(self.get_help_message())
            return self.prompt_for_value(ctx)

        if value == self.CHARACTER_IGNORE_DEFAULT and source is click.core.ParameterSource.PROMPT:
            # This means the user does not want to set a specific value for this option, so the ``!`` character is
            # translated to ``None`` and processed as normal. If the option is required, a validation error will be
            # raised further down below, forcing the user to specify a valid value.
            value = None

        try:
            return super().process_value(ctx, value)
        except click.BadParameter as exception:
            if source is click.core.ParameterSource.PROMPT and self.is_interactive(ctx):
                if isinstance(exception, click.MissingParameter):
                    click.echo(f'Error: {self._prompt} has to be specified')
                else:
                    click.echo(f'Error: {exception}')
                return self.prompt_for_value(ctx)
            raise

    def get_help_message(self) -> str:
        """Return a message to be displayed for in-prompt help."""
        message = self.help or f'Expecting {self.type.name}'

        shell_complete: t.Callable[[click.ParamType, click.Context | None, str], list[CompletionItem]] = getattr(
            self.type, 'shell_complete', lambda x, y, z: []
        )
        choices = shell_complete(self.type, None, '')
        choices_string = []

        for choice in choices:
            if choice.value and choice.help:
                choices_string.append(f' * {choice.value:<12} {choice.help}')
            elif choice.value:
                choices_string.append(f' * {choice.value}')

        if any(choices_string):
            message += '\nSelect one of:\n'
            message += '\n'.join([choice for choice in choices_string if choice.strip()])

        return message

    def get_default(self, ctx: click.Context, call: bool = True) -> t.Any | None:
        """Provides the functionality of :meth:`click.Option.get_default`"""
        if ctx.resilient_parsing:
            return None

        if self._contextual_default is not None:
            default = self._contextual_default(ctx)
        else:
            default = super().get_default(ctx, call=call)

        try:
            default = self.type.deconvert_default(default)  # type: ignore[attr-defined]
        except AttributeError:
            pass

        return default

    @staticmethod
    def is_interactive(ctx: click.Context) -> bool:
        """Return whether the command is being run non-interactively.

        This is the case if the ``non_interactive`` parameter in the context is set to ``False``.

        :return: ``True`` if being run interactively, ``False`` otherwise.
        """
        return not ctx.params.get('non_interactive', False)


class TemplateInteractiveOption(InteractiveOption):
    """Sub class of ``InteractiveOption`` that uses template file for input instead of simple inline prompt.

    This is useful for options that need to be able to specify multiline string values.
    """

    def __init__(self, param_decls: Sequence[str] | None = None, **kwargs: t.Any):
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

    def prompt_for_value(self, ctx: click.Context) -> t.Any:
        """Replace the basic prompt with a method that opens a template file in an editor."""
        from aiida.cmdline.utils.multi_line_input import edit_multiline_template

        if not self.is_interactive(ctx):
            return self.get_default(ctx)

        if self._prompt_fn is not None and self._prompt_fn(ctx) is False:
            return None

        kwargs = {'value': self.get_default(ctx) or '', 'header': self.header, 'footer': self.footer}
        return edit_multiline_template(self.template, extension=self.extension, **kwargs)

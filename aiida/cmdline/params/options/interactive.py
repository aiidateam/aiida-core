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
.. module::interactive
    :synopsis: Tools and an option class for interactive parameter entry with
    additional features such as help lookup.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.utils import echo
from .conditional import ConditionalOption


def noninteractive(ctx):
    """check context for non_interactive flag"""
    return ctx.params.get('non_interactive')


def string_wrapper(msg, max_length=100):
    """Wraps a string into multiple lines according to ``max_length``"""
    words = msg.split(' ')
    lines = ['']
    for word in words:
        if not lines[-1]:
            lines[-1] = word
        elif len(lines[-1]) + len(word) + 1 <= max_length:
            lines[-1] += ' ' + word
        else:
            lines.append(word)
    return lines


class InteractiveOption(ConditionalOption):
    """
    Intercepts certain keyword arguments to circumvent :mod:`click`'s prompting
    behaviour and define a more feature-rich one

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
            click.echo('Labeling with label: {}'.format(label))
    """
    PROMPT_COLOR = 'yellow'

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
        super(InteractiveOption, self).__init__(param_decls=param_decls, **kwargs)

        self.prompt_fn = prompt_fn

        # I check that a prompt was actually defined.
        # I do it after calling super so e.g. 'self.name' is defined
        if not self._prompt:
            raise TypeError(
                "Interactive options need to have a prompt specified, but '{}' does not have a prompt defined".format(
                    self.name))

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

    def get_default(self, ctx):
        """disable :mod:`click` from circumventing prompting when a default value exists"""
        return None

    def _get_default(self, ctx):
        """provides the functionality of :func:`click.Option.get_default`"""
        if self._contextual_default is not None:
            return self._contextual_default(ctx)

        return super(InteractiveOption, self).get_default(ctx)

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
            confirmation_prompt=self.confirmation_prompt)

    def ctrl_help(self):
        """control behaviour when help is requested from the prompt"""
        echo.echo_info(self.format_help_message())

    def format_help_message(self):
        """
        format the message to be displayed for in-prompt help.

        gives a list of possibilities for parameter types that support completion
        """
        msg = self.help or 'Expecting {}'.format(self.type.name)
        choices = getattr(self.type, 'complete', lambda x, y: [])(None, '')
        if choices:
            choice_table = []
            msg += '\nSelect one of:\n'
            for choice in choices:
                if isinstance(choice, tuple):
                    choice_table.append('\t{:<12} {}'.format(*choice))
                else:
                    choice_table.append('\t{:<12}'.format(choice))
            msg += '\n'.join(choice_table)
        return msg

    def full_process_value(self, ctx, value):
        """
        catch errors raised by ConditionalOption in order to adress them in
        the callback
        """
        try:
            value = super(InteractiveOption, self).full_process_value(ctx, value)
        except click.MissingParameter:
            pass
        return value

    def safely_convert(self, value, param, ctx):
        """
        convert without raising, instead print a message if fails

        :return: Tuple of ( success (bool), converted value )
        """
        successful = False
        try:
            value = self.type.convert(value, param, ctx)
            successful = True
        except click.BadParameter as err:
            echo.echo_error(str(err))
            self.ctrl_help()
        return successful, value

    def simple_prompt_loop(self, ctx, param, value):
        """prompt until successful conversion. dispatch control sequences"""
        if not hasattr(ctx, 'prompt_loop_info_printed'):
            echo.echo_info('enter "?" for help')
            ctx.prompt_loop_info_printed = True
        while 1:
            # prompt
            value = self.prompt_func(ctx)
            if value in self._ctrl:
                # dispatch - e.g. show help
                self._ctrl[value]()
                continue
            else:
                # try to convert, if unsuccessful continue prompting
                successful, value = self.safely_convert(value, param, ctx)
                if successful:
                    return value

    def after_callback(self, ctx, param, value):
        """if a callback was registered on init, call it and return it's value"""
        if self._after_callback:
            return self._after_callback(ctx, param, value)
        return value

    def prompt_callback(self, ctx, param, value):
        """decide wether to initiate the prompt_loop or not"""

        # From click.core.Context:
        # if resilient_parsing is enabled then Click will
        # parse without any interactivity or callback
        # invocation.
        # Therefore if this flag is set, we should not
        # do any prompting.
        if ctx.resilient_parsing:
            return None

        # a value was given on the command line: then  just go with validation
        if value is not None:
            return self.after_callback(ctx, param, value)

        # The same if the user specified --non-interactive
        if noninteractive(ctx):
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
            value = self.prompt_loop(ctx, param, value)
        else:
            # There is a prompt_fn function and returns False (i.e. should not ask for this value
            # We then set the value to None
            value = None

        # And then we call the callback
        return self.after_callback(ctx, param, value)


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

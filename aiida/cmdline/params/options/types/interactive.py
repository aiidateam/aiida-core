# -*- coding: utf8 -*-
"""
.. module::interactive
    :synopsis: Tools and an option class for interactive parameter entry with
    additional features such as help lookup.
"""

import click

from aiida.cmdline.params.options.types.conditional import ConditionalOption


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

    Usage::

        import click

        @click.command()
        @click.option('label', prompt='Label', cls=InteractiveOption)
        def foo(label):
            click.echo('Labeling with label: {}'.format(label))
    """

    def __init__(self, param_decls=None, switch=None, empty_ok=False, **kwargs):
        """
        :param param_decls: relayed to :class:`click.Option`
        :param switch: sequence of parameter names
        """
        # intercept prompt kwarg
        self._prompt = kwargs.pop('prompt', None)
        if kwargs.get('required', None):
            required_fn = kwargs.get('required_fn', lambda ctx: True)
            kwargs['required_fn'] = lambda ctx: noninteractive(ctx) and required_fn(ctx)

        # super
        super(InteractiveOption, self).__init__(param_decls=param_decls, **kwargs)

        # other kwargs
        self.switch = switch
        self.empty_ok = empty_ok

        # set callback
        if self._prompt:
            self._after_callback = self.callback
            self.callback = self.prompt_callback

        # set controll strings that trigger special features from the input prompt
        self._ctrl = {'?': self.ctrl_help}

        # set prompting type
        self.prompt_loop = self.simple_prompt_loop

    def get_default(self, ctx):
        """disable :mod:`click` from circumventing prompting when a default value exists"""
        return None

    def _get_default(self, ctx):
        """provides the functionality of :func:`click.Option.get_default`"""
        return super(InteractiveOption, self).get_default(ctx)

    def prompt_func(self, ctx):
        """prompt function with args set"""
        return click.prompt(
            self._prompt,
            default=self._get_default(ctx),
            hide_input=self.hide_input,
            confirmation_prompt=self.confirmation_prompt)

    def ctrl_help(self):
        """control behaviour when help is requested from the prompt"""
        click.echo(self.format_help_message())

    def format_help_message(self):
        """
        format the message to be displayed for in-prompt help.

        gives a list of possibilities for parameter types that support completion
        """
        msg = self.help or 'Expecting {}'.format(self.type.name)
        choices = getattr(self.type, 'complete', lambda x, y: [])(None, '')
        if choices:
            msg += '\n\tone of:\n'
            choice_table = ['\t\t{:<12} {}'.format(*choice) for choice in choices]
            msg += '\n'.join(choice_table)
        msg = click.style('\t' + msg, fg='green')
        return msg

    def unacceptably_empty(self, value):
        """check if the value is empty and should not be passed on to conversion"""
        result = not value and not isinstance(value, bool)
        if self.empty_ok:
            return False
        return result

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
            click.echo(err.message)
        return successful, value

    def simple_prompt_loop(self, ctx, param, value):
        """prompt until successful conversion. dispatch control sequences"""
        while 1:
            # prompt
            value = self.prompt_func(ctx)
            if value in self._ctrl:
                # dispatch
                self._ctrl[value]()
            elif self.unacceptably_empty(value):
                # repeat prompting without trying to convert
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

        # a value was given
        if value is not None:
            return self.after_callback(ctx, param, value)

        # parameter is not reqired anyway
        if not self.is_required(ctx):
            return self.after_callback(ctx, param, value)

        # help option was passed on the cmdline
        if ctx.params.get('help'):
            return self.after_callback(ctx, param, value)

        # no value was given
        try:
            # try to convert None
            value = self.after_callback(ctx, param, self.type.convert('', param, ctx))
            # if conversion comes up empty, make sure empty is acceptable
            if self.unacceptably_empty(value):
                raise click.MissingParameter(param=param)

        except (click.MissingParameter, click.BadParameter):
            # no value was given but a value is required
            # check for BadParameter too, because convert might not check for None specifically

            # no prompting allowed
            if noninteractive(ctx):
                # either get a default value and return ...
                default = self._get_default(ctx) or self.default
                if default is not None:
                    return self.type.convert(default, param, ctx)
                else:
                    # ... or raise Missing Parameter
                    raise click.MissingParameter()
            # prompting allowed
            value = self.prompt_loop(ctx, param, value)
        return value


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

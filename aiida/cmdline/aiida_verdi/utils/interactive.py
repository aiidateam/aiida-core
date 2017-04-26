# -*- coding: utf8 -*-
"""
.. module::interactive
    :synopsis: Tools and an option class for interactive parameter entry with
    additional features such as help lookup.
"""

import click

from aiida.cmdline.aiida_verdi.utils.conditional import ConditionalOption


def noninteractive(ctx):
    """check context for non_interactive flag"""
    return ctx.params.get('non_interactive')


def string_wrapper(s, max_length=100):
    words = s.split(' ')
    lines = ['']
    for w in words:
        if not lines[-1]:
            lines[-1] = w
        elif len(lines[-1]) + len(w) + 1 <= max_length:
            lines[-1] += ' ' + w
        else:
            lines.append(w)
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
        '''intercept prompt kwarg'''
        self._prompt = kwargs.pop('prompt', None)
        self._editor = kwargs.pop('editor', None)
        if kwargs.get('required', None):
            required_fn = kwargs.get('required_fn', lambda ctx: True)
            kwargs['required_fn'] = lambda ctx: noninteractive(ctx) and required_fn(ctx)

        '''super'''
        super(InteractiveOption, self).__init__(param_decls=param_decls, **kwargs)

        '''other kwargs'''
        self.switch = switch
        self.empty_ok = empty_ok

        '''set callback'''
        if self._prompt:
            self._after_callback = self.callback
            self.callback = self.prompt_callback

        '''set controll strings that trigger special features from the input prompt'''
        self._ctrl = {'?': self.ctrl_help}

        '''set prompting type'''
        self.prompt_loop = self.simple_prompt_loop
        if self._editor:
            self.prompt_loop = self.editor_loop

    def get_default(self, ctx):
        """disable :mod:`click` from circumventing prompting when a default value exists"""
        return None

    def _get_default(self, ctx):
        """provides the functionality of :func:`click.Option.get_default`"""
        return super(InteractiveOption, self).get_default(ctx)

    def prompt_func(self, ctx):
        """prompt function with args set"""
        return click.prompt(self._prompt, default=self._get_default(ctx), hide_input=self.hide_input, confirmation_prompt=self.confirmation_prompt)

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
        else:
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
        except click.BadParameter as e:
            click.echo(e.message)
        return successful, value

    def simple_prompt_loop(self, ctx, param, value):
        """prompt until successful conversion. dispatch control sequences"""
        while 1:
            '''prompt'''
            value = self.prompt_func(ctx)
            if value in self._ctrl:
                '''dispatch'''
                self._ctrl[value]()
            elif self.unacceptably_empty(value):
                '''repeat prompting without trying to convert'''
                continue
            else:
                '''try to convert, if unsuccessful continue prompting'''
                successful, value = self.safely_convert(value, param, ctx)
                if successful:
                    return value

    def editor_loop(self, ctx, param, value):
        """
        open an editor analog to git commit for multiline input but in a loop until the result is verified.
        This method is currently in development and may be instable / incorrect.
        """
        while 1:
            '''prompt'''
            marker = '#= All lines beginning with "#=" will be ignored'
            helper = [marker, self._prompt] + string_wrapper(self.format_help_message(), 50)
            template = '\n' + '\n#= '.join(helper)
            inserttxt = template
            if isinstance(self._editor, list):
                '''editor will be used to set muliple values'''
                multiedit = True
                inserttxt = '#= ' + '\n\n#= '.join(self._editor) + '\n' + template
            mlinput = click.edit(inserttxt)
            click.echo('')
            click.echo(mlinput)
            if mlinput:
                '''editor was saved and quitted'''
                value = mlinput.replace(template, '')
                click.echo('')
                click.echo(value)
                if multiedit:
                    '''separate the values using the given separator lines'''
                    values = []
                    seplines = self._editor[::-1]
                    # ~ value = value.split(seplines.pop())[1]
                    for sep in seplines:
                        value, l = value.split('#= ' + sep)
                        click.echo('{} <-> {}'.format(value, l))
                        values.append(l.strip())
                        click.echo(values)
                    value = values[::-1]
            if self.unacceptably_empty(value):
                '''reopen editor without trying to convert'''
                continue
            else:
                '''try to convert, reopen editor if unsuccessful'''
                successful, value = self.safely_convert(value, param, ctx)
                if successful:
                    return value

    def after_callback(self, ctx, param, value):
        """if a callback was registered on init, call it and return it's value"""
        if self._after_callback:
            return self._after_callback(ctx, param, value)
        else:
            return value

    def prompt_callback(self, ctx, param, value):
        """decide wether to initiate the prompt_loop or not"""

        '''a value was given'''
        if value is not None:
            return self.after_callback(ctx, param, value)

        '''parameter is not reqired anyway'''
        if not self.is_required(ctx):
            return self.after_callback(ctx, param, value)

        '''help option was passed on the cmdline'''
        if ctx.params.get('help'):
            return self.after_callback(ctx, param, value)

        '''no value was given'''
        try:
            '''try to convert None'''
            value = self.after_callback(ctx, param, self.type.convert(value, param, ctx))
            '''if conversion comes up empty, make sure empty is acceptable'''
            if self.unacceptably_empty(value):
                raise click.MissingParameter(param=param)

        except Exception as e:
            '''
            no value was given but a value is required

            this needs to be Exception because generally convert does not
            check for None and is allowed to raise any exception when
            encountering it
            '''

            '''no prompting allowed'''
            if noninteractive(ctx):
                '''either get a default value and return ...'''
                default = self._get_default(ctx) or self.default
                if default is not None:
                    return self.type.convert(default, param, ctx)
                else:
                    '''... or raise Missing Parameter'''
                    raise click.MissingParameter()
            '''prompting allowed'''
            value = self.prompt_loop(ctx, param, value)
        return value


def opt_prompter(ctx, cmd, givenkwargs, oldvalues=None):
    cmdparams = {i.name: i for i in cmd.params}
    def opt_prompt(opt, prompt, default=None):
        if not givenkwargs[opt]:
            optobj = cmdparams[opt]
            optobj._prompt = prompt
            optobj.default = default or oldvalues.get(opt)
            return optobj.prompt_loop(ctx, optobj, givenkwargs[opt])
        else:
            return givenkwargs[opt]
    return opt_prompt

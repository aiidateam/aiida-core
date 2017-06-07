#-*- coding: utf8 -*-
"""
utilities for verdi commandline
"""
import click
from click_spinner import spinner as cli_spinner


def load_dbenv_if_not_loaded(**kwargs):
    """
    load dbenv if necessary, run spinner meanwhile to show command hasn't crashed
    """
    with cli_spinner():
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv(**kwargs)


def aiida_dbenv(function):
    """
    a function decorator that loads the dbenv if necessary before running the function
    """
    def decorated_function(*args, **kwargs):
        """load dbenv if not yet loaded, then run the original function"""
        load_dbenv_if_not_loaded()
        return function(*args, **kwargs)
    return decorated_function


@aiida_dbenv
def get_code(code_id):
    """
    Get a Computer object with given identifier, that can either be
    the numeric ID (pk), or the label (if unique).

    .. note:: If an string that can be converted to an integer is given,
        the numeric ID is verified first (therefore, is a code A with a
        label equal to the ID of another code B is present, code A cannot
        be referenced by label).
    """
    import sys

    from aiida.common.exceptions import NotExistent, MultipleObjectsError
    from aiida.orm import Code as AiidaOrmCode

    try:
        return AiidaOrmCode.get_from_string(code_id)
    except (NotExistent, MultipleObjectsError) as e:
        click.echo(e.message, err=True)
        sys.exit(1)


@aiida_dbenv
def get_code_data(django_filter=None):
    """
    Retrieve the list of codes in the DB.
    Return a tuple with (pk, label, computername, owneremail).

    :param django_filter: a django query object (e.g. obtained
        with Q()) to filter the results on the AiidaOrmCode class.
    """
    from aiida.orm import Code as AiidaOrmCode
    from aiida.orm.querybuilder import QueryBuilder

    qb = QueryBuilder()
    qb.append(AiidaOrmCode, project=['id', 'label', 'description'])
    qb.append(type='computer', computer_of=AiidaOrmCode, project=['name'])
    qb.append(type='user', creator_of=AiidaOrmCode, project=['email'])

    return sorted(qb.all())


def create_code(**kwargs):
    """
    creates a code from kwargs

    :kwarg label: label
    :kwarg description: description
    :kwarg installed: switch wether to use local_executable or remote_computer_exec
    :kwarg input_plugin: name for the default input plugin
    :kwarg code_folder: folder containing the code if is_local == True
    :kwarg code_rel_path: the relative path from code_folder to the executable
    :kwarg computer: the remote computer running the code if is_local == False
    :kwarg remote_abs_path: the absolute path on computer to the executable
    :kwarg prepend_text: bash code to be run before execution
    :kwarg append_text: bash code to be run after execution
    """
    import os
    from os.path import realpath
    from os.path import join as pjoin

    from aiida.orm import Code as AiidaOrmCode

    '''local / remote code'''
    is_local = not kwargs['installed']
    if is_local:
        '''local code'''
        code_folder = kwargs['code_folder']
        code_rel_path = kwargs['code_rel_path']
        file_list = [realpath(pjoin(code_folder, f)) for f in os.listdir(code_folder)]
        code = AiidaOrmCode(local_executable=code_rel_path, files=file_list)
    else:
        '''remote code'''
        computer = kwargs['computer']
        remote_abs_path = kwargs['remote_abs_path']
        code = AiidaOrmCode(remote_computer_exec=(computer, remote_abs_path))

    '''either way'''
    code.label = kwargs['label']
    code.description = kwargs['description']
    code.set_input_plugin_name(kwargs['input_plugin'])
    code.set_prepend_text(kwargs['prepend_text'])
    code.set_append_text(kwargs['append_text'])

    return code


@aiida_dbenv
def input_plugin_list():
    """return a list of available input plugins"""
    from aiida.common.pluginloader import existing_plugins
    from aiida.orm.calculation.job import JobCalculation
    return [p.rsplit('.', 1)[0] for p in existing_plugins(JobCalculation, 'aiida.orm.calculation.job')]


@aiida_dbenv
def computer_name_list():
    """
    Retrieve the list of computers in the DB.

    ToDo: use an API or cache the results, sometime it is quite slow!
    """
    with cli_spinner():
        from aiida.orm.querybuilder import QueryBuilder
        qb = QueryBuilder()
        qb.append(type='computer', project=['name'])
        if qb.count() > 0:
            return list(zip(*qb.all())[0])
        else:
            return None


def print_list_res(qb_query, show_owner):
    """print a list of QueryBuilder results"""
    if qb_query.count > 0:
        for tuple_ in qb_query.all():
            if len(tuple_) == 3:
                (pk, label, useremail) = tuple_
                computername = None
            elif len(tuple_) == 4:
                (pk, label, useremail, computername) = tuple_
            else:
                click.echo("Wrong tuple size")
                return

            if show_owner:
                owner_string = " ({})".format(useremail)
            else:
                owner_string = ""
            if computername is None:
                computernamestring = ""
            else:
                computernamestring = "@{}".format(computername)
            click.echo("* pk {} - {}{}{}".format(
                pk, label, computernamestring, owner_string))
    else:
        click.echo("# No codes found matching the specified criteria.")


def default_callback(ctx, param, value):
    """return bool(value), value"""
    return bool(value), value


def single_value_prompt(ctx, param, value, prompt=None, default=None, callback=default_callback, suggestions=None, **kwargs):
    """
    prompt for a single value on the commandline

    :param ctx: context object, passed by click on callback
    :param param: parameter object, passed by click on callback
    :param value: parameter value, passed by click on callback
    :kwarg prompt: the prompt displayed on the input line
    :kwarg default: the default input (pressing return on an empty line)
    :kwarg suggestions: callable that returns a list of suggestions
    :kwargs callback: callable that returns (valid, value) where valid is True if value is valid and value is the (converted) input value
    :return: value as converted by callback
    """
    import pprint
    keep_prompting = True
    _help = param.help or 'invalid input'
    if suggestions:
        _help += '\none of:\n' + pprint.pformat(suggestions(), indent=3)
    while keep_prompting:
        inp = click.prompt(prompt, default=default)
        if inp == '?':
            click.echo(_help)
        else:
            valid, converted_value = callback(ctx, param, inp)
            if valid:
                value = converted_value
                break
            else:
                click.echo(_help)
    return value


def multi_line_prompt(ctx, param, value, prompt=None, header=True, **kwargs):
    """
    prompt for multiple lines of input on the commandline

    :kwarg bool header: controls if the header message should be printed
    :return: list of lines
    """
    click.echo('')
    click.echo(prompt)
    '''print header if requested'''
    if header:
        click.echo('-------------------------------------------------')
        click.echo('| multiline input, ? for help, \\quit to accept |')
        click.echo('-------------------------------------------------')
    lines = []
    keep_prompting = True
    _help = param.help or 'multline text input'
    while keep_prompting:
        line = click.prompt('line {:<3}'.format(len(lines)), default='', show_default=False)
        if line == '\\quit':
            break
        if line == '\\restart':
            click.echo('-------------------------------------------------')
            lines = []
        elif line == '?':
            click.echo(_help)
            click.echo('\\quit to conclude and accept, \\restart to start over')
            click.echo('-------------------------------------------------')
        else:
            lines.append(line)
    return lines


def prompt_with_help(prompt=None, default=None, suggestions=None, callback=default_callback, ni_callback=None, prompt_loop=single_value_prompt, **kwargs):
    """
    create a callback function to prompt for input which displays help if '?' is entered

    :kwarg prompt: the prompt displayed on the input line
    :kwarg default: the default input (pressing return on an empty line), passed to the prompt_loop callback
    :kwarg suggestions: callable that returns a list of suggestions, passed to prompt_loop
    :kwargs callback: callable that returns (valid, value) where valid is True if value is valid and value is the (converted) input value
    :kwargs ni_callback: alternative callback to be used if --non-interactive is set
    :kwargs prompt_loop: callback that prompts the commandline for input
    :return: the value as converted by callback or ni_callback if given or as entered on the commandline if not or as returned by prompt_loop if value was not considered valid
    """
    def prompt_callback(ctx, param, value):
        '''gather relevant context info'''
        non_interactive = ctx.params.get('non_interactive')
        debug = ctx.params.get('debug')

        '''print debug info if flag is set'''
        if debug:
            click.echo('')
            click.echo('parsing option: ' + param.name)
            click.echo('context: ' + str(ctx))
            click.echo('parameter: ' + str(param))
            click.echo('value: ' + repr(value))

        '''validate and optionally convert'''
        if non_interactive and ni_callback:
            valid_input, value = ni_callback(ctx, param, value)
        elif callback:
            valid_input, value = callback(ctx, param, value)
        else:
            valid_input = bool(value)

        '''to prompt or not to prompt'''
        if not valid_input and not non_interactive:
            '''prompting necessary'''
            value = prompt_loop(ctx, param, value, prompt=prompt, default=default, suggestions=suggestions, callback=callback, **kwargs)
        '''more debug info'''
        if debug:
            click.echo('recieved: ' + str(value))
        return value
    return prompt_callback


def prompt_help_loop(prompt=None, suggestions=None):
    """prompt for a value, display help at ?, use decorated function for validation"""
    def decorator(validator_func):
        """decorate a validator function with a loop prompting for a value, displaying help at ?"""
        def decorated_validator(ctx, param, value):
            """promtp for a value, display help at ?, use inner function for validation"""
            prevalue = validator_func(ctx, param, value)
            if isinstance(ctx.obj, dict):
                if ctx.obj.get('nocheck'):
                    return prevalue or 'UNUSED'
            _help = param.help or 'invalid input'
            if suggestions:
                _help += '\none of:\n\t' + '\n\t'.join(suggestions())
            if not ctx.params.get('non_interactive'):
                if isinstance(ctx.obj, dict):
                    multiline = ctx.obj.get('multiline', [])
                    click.echo(ctx.obj)
                    while param in multiline:
                        value = decorated_validator(ctx, param, click.prompt(prompt or param.prompt))
                    value = ctx.obj.get('multiline_val_'+param.opts[0])
                while validator_func(ctx, param, value) is None or value == '?':
                    click.echo(_help)
                    value = decorated_validator(ctx, param, click.prompt(prompt or param.prompt, default=param.default))
            value = validator_func(ctx, param, value)
            if ctx.params.get('non_interactive') and not value:
                raise click.MissingParameter(ctx=ctx, param=param, param_hint='{} {}'.format(param.opts, _help))
            return value
        return decorated_validator
    return decorator


class base_validator(object):
    """
    Base class for validators for click options

    automatically provides a non-raising validation method
    subclasses must implement validate to raise click.BadParam if validation
    fails.

    :param raise_exceptions: the default behaviour for __call__
    :required_if: callable with signature (ctx, param) which returns True
        if the parameter is required and False if not, in which case no validation
        will take place
    """
    def __init__(self, raise_exceptions=False, required_if=None):
        self.raise_exceptions = raise_exceptions
        self.required_if = required_if

    def __call__(self, ctx, param, value, raise_exceptions=None):
        """check if the path is needed and if yes, validate"""

        if raise_exceptions is None:
            raise_exceptions = self.raise_exceptions

        '''gather context info'''
        if self.required_if is not None:
            required = self.required_if(ctx, param)
        else:
            required = True
        debug = ctx.params.get('debug')

        '''debug info'''
        if debug:
            click.echo('\trequired: ' + str(required))
            click.echo('\traising: ' + str(raise_exceptions))

        '''No validation needed'''
        if not required:
            return True, value

        '''validation needed'''
        result = False, value
        if value:
            '''try to convert'''
            try:
                value = self.validate(ctx, param, value)
                result = True, value
            except click.BadParameter as e:
                '''conversion failed'''
                if raise_exceptions:
                    raise e
                click.echo(e.format_message(), err=True)
                result = False, value
        else:
            '''no value given'''
            if raise_exceptions:
                raise click.MissingParameter(param=param)
        if debug:
            click.echo('\tconverted value: ' + str(result[1]))
            click.echo('\tvalid: ' + str(result[0]))
        return result

    def validate(self, ctx, param, value):
        """only checks if any value was given at all"""
        if value is None:
            raise click.MissingParameter(param=param)
        else:
            return value

    def nothrow(self, ctx, param, value):
        """validate without raising exceptions for invalid arguments"""
        return self.__call__(ctx, param, value, raise_exceptions=False)

    def throw(self, ctx, param, value):
        """validate, raising exceptions for invalid arguments"""
        return self.__call__(ctx, param, value, raise_exceptions=True)


class path_validator(base_validator):
    """
    wrapper around click.Path to be used in custom callbacks
    """
    def __init__(self, is_abs=False, expand_user=True, raise_exceptions=False, required_if=None, prefix_opt=None, **kwargs):
        super(path_validator, self).__init__(raise_exceptions=raise_exceptions, required_if=required_if)
        """relay kwargs to click.path"""
        self.path_t = click.Path(**kwargs)
        self.expand_user = expand_user
        self.is_abs = is_abs
        self.prefix_opt = prefix_opt

    def validate(self, ctx, param, value):
        """validate a path argument, raising click.BadParameter if invalid"""
        if self.expand_user:
            from os.path import expanduser
            value = expanduser(value)
        if self.is_abs:
            from os.path import isabs
            if not isabs(value):
                raise click.BadParameter('Must be an absolute path!', param=param)
        if self.prefix_opt:
            from os.path import join as pjoin
            value = pjoin(ctx.params.get(self.prefix_opt), value)
        value = self.path_t.convert(value, param, ctx)
        return value


class computer_validator(base_validator):
    """check that the given argument corresponds to a computer in the user database"""
    def __init__(self, required_if=None, raise_exceptions=False):
        super(computer_validator, self).__init__(raise_exceptions=raise_exceptions, required_if=required_if)

    @aiida_dbenv
    def validate(self, ctx, param, value):
        """validate computer argument in prompt callback"""
        '''get a list of computers to verify the given one is in there'''
        from aiida.orm.computer import Computer
        computers = computer_name_list()
        if ctx.params.get('debug'):
            click.echo('\tpossible computers: ' + str(computers))
            click.echo('\tvalid: ' + str(value in computers))
        if value not in computers:
            raise click.BadParameter('{} is not a computer in your database!'.format(value), param=param)
        return Computer.get(value)


class InteractiveOption(click.Option):
    """
    registers a callback for alternative prompting behaviour

    :kwarg multiline: if True, the multiline prompt will be used
    """
    def __init__(self, param_decls=None, multiline=False, **attrs):
        self.prompt_string = attrs.pop('prompt')
        self.multiline = multiline
        super(InteractiveOption, self).__init__(param_decls=param_decls, **attrs)
        if self.multiline:
            self.prompt_loop = multi_line_prompt
        else:
            self.prompt_loop = self.single_value_prompt

        self.after_prompt_callback = self.callback or None
        self.callback = self.argument_callback
        self.max_suggestions = 10

    def argument_callback(self, ctx, param, value, **kwargs):
        '''gather relevant context info'''
        non_interactive = ctx.params.get('non_interactive')
        debug = ctx.params.get('debug')

        '''print debug info if flag is set'''
        if debug:
            click.echo('')
            click.echo('parsing option: ' + param.name)
            click.echo('context: ' + str(ctx))
            click.echo('parameter: ' + str(param))
            click.echo('value: ' + repr(value))

        '''validate and optionally convert'''
        if non_interactive and hasattr(self.type, 'unsafe_convert'):
            valid_input, value = self.type.unsafe_convert(value, param, ctx)
        elif hasattr(self.type, 'safe_convert'):
            valid_input, value = self.type.safe_convert(value, param, ctx)
        else:
            valid_input = value is not None

        '''to prompt or not to prompt'''
        if not valid_input and not non_interactive:
            '''prompting necessary'''
            value = self.prompt_loop(ctx, param, value, **kwargs)
        '''more debug info'''
        if debug:
            click.echo('recieved: ' + str(value))

        if self.after_prompt_callback:
            value = self.after_prompt_callback(ctx, param, value)
        return value

    def single_value_prompt(self, ctx, param, value, **kwargs):
        """
        prompt for a single value on the commandline

        :param ctx: context object, passed by click on callback
        :param param: parameter object, passed by click on callback
        :param value: parameter value, passed by click on callback
        :return: value as converted by callback
        """
        keep_prompting = True
        _help = self.help or 'invalid input'
        if hasattr(self.type, 'get_possibilities'):
            possibilities = self.type.get_possibilities()
            if possibilities:
                if isinstance(possibilities[0], tuple):
                    item = '{:<12} {}'
                    suggestions = [item.format(*p) for p in possibilities]
                else:
                    suggestions = possibilities
                if len(suggestions) > self.max_suggestions:
                    suggestions = suggestions[:self.max_suggestions]
                    suggestions += ['...']
            _help += '\none of:\n\t' + '\n\t'.join(suggestions)
        if keep_prompting:
            click.echo(_help)
        while keep_prompting:
            value = click.prompt(self.prompt_string, default=self.default)
            if value == '?':
                click.echo(_help)
            else:
                valid, converted_value = self.type.safe_convert(value, param, ctx)
                if valid:
                    value = converted_value
                    break
                else:
                    click.echo(_help)
        return value

#-*- coding: utf8 -*-
"""
click parameter type that registers a callback for prompting with help

!!!! this module is obsolete and will be removed !!!!
"""

import click


class PromptHelp(click.BadParameter):
    def show(self, file=None):
        click.echo(self.format_message())


def _make_interactive_convert(convert_func):
    def interactive_convert(self, value, param, ctx):
        if ctx.params.get('debug'):
            click.echo('ExperimentalParam - Convert')
            click.echo('name:  ' + str(param.name))
            click.echo('type:  ' + str(param.type))
            click.echo('value: ' + str(value))
        if value == '?':
            raise PromptHelp(self.get_missing_message(param))
        else:
            return convert_func(self, value, param, ctx)
    return interactive_convert


class Interactivity(type):
    """Interactivity metaclass"""
    def __new__(mcs, name, bases, dct):
        if 'convert' in dct:
            dct['convert'] = _make_interactive_convert(dct['convert'])
        return type.__new__(mcs, name, bases, dct)


class InteractiveParam(click.ParamType):
    __metaclass__ = Interactivity

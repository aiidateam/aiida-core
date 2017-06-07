# -*- coding: utf-8 -*-
"""
standard arguments for consistency throughout the verdi commandline
"""
import click
from aiida.cmdline.aiida_verdi.param_types.code import CodeParam, CodeNameParam
from aiida.cmdline.aiida_verdi.param_types.computer import ComputerParam
from aiida.cmdline.aiida_verdi.param_types.jobcalc import JobCalcParam
from aiida.cmdline.aiida_verdi.param_types.plugin import PluginParam
from aiida.cmdline.aiida_verdi.param_types.node import NodeParam


class overridable_argument(object):
    """
    wrapper around click argument that allows for defaults to be stored for reuse
    and for some arguments to be overriden later.
    """
    def __init__(self, *args, **kwargs):
        """
        store defaults
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """
        override kwargs and return click argument
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)
        self.args += args
        return click.argument(*self.args, **kw_copy)


node = overridable_argument('node', metavar='NODE', type=NodeParam())
code = overridable_argument('code', metavar='CODE', type=CodeParam())
codelabel = overridable_argument('name', type=CodeNameParam())
computer = overridable_argument('computer', type=ComputerParam())
calculation = overridable_argument('calc', metavar='CALCULATION', type=JobCalcParam())
input_plugin = overridable_argument('input_plugin', type=PluginParam(category='calculations'))
comment_id = overridable_argument('comment-id', type=int)

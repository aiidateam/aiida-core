# -*- coding: utf-8 -*-
"""
JobCalculation Parameter type for arguments and options
"""
import click
from click_completion import startswith
from click_spinner import spinner as cli_spinner

from aiida.cmdline.aiida_verdi.verdic_utils import aiida_dbenv
from aiida.cmdline.aiida_verdi.param_types.node import NodeParam


class JobCalcParam(NodeParam):
    name = 'aiida calculation item'

    @property
    @aiida_dbenv
    def node_type(self):
        from aiida.orm import JobCalculation
        return JobCalculation

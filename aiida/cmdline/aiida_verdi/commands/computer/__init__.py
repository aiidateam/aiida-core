# -*- coding: utf-8 -*-
"""
assemble computer subcommands
"""
from aiida.cmdline.aiida_verdi.commands.computer.setup import setup
from aiida.cmdline.aiida_verdi.commands.computer.configure import configure


__all__ = ['configure', 'setup']

#-*- coding: utf8 -*-
"""
verdi quicksetup backport wrapper
"""
from aiida.cmdline.aiida_verdi.commands.quicksetup import quicksetup
from aiida.cmdline.baseclass import VerdiCommand


class Quicksetup(VerdiCommand):
    """
    VerdiCommand wrapper for the quicksetup backport from DropD/aiida-verdi
    """
    def run(self, *args):
        ctx = quicksetup.main(args=args, standalone_mode=False, prog_name='verdi quicksetup')

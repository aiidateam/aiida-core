# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_data


class Data(VerdiCommandWithSubcommands):
    """
    Setup and manage data specific types

    There is a list of subcommands for managing specific types of data.
    For instance, 'data upf' manages pseudopotentials in the UPF format.
    """

    def __init__(self):
        from aiida.backends.utils import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.cmdline.commands.data import upf
        from aiida.cmdline.commands.data import structure
        from aiida.cmdline.commands.data import bands
        from aiida.cmdline.commands.data import cif
        from aiida.cmdline.commands.data import trajectory
        from aiida.cmdline.commands.data import parameter
        from aiida.cmdline.commands.data import array
        from aiida.cmdline.commands.data import remote

        self.valid_subcommands = {
            'upf': (self.cli, self.complete_none),
            'structure': (self.cli, self.complete_none),
            'bands': (self.cli, self.complete_none),
            'cif': (self.cli, self.complete_none),
            'trajectory': (self.cli, self.complete_none),
            'parameter': (self.cli, self.complete_none),
            'array': (self.cli, self.complete_none),
            'remote': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()

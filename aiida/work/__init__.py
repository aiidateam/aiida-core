# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.work.workfunction import workfunction
from aiida.work.workchain import WorkChain
from aiida.work.run import async, run, submit
import aiida.work.globals
from aiida.work.globals import \
    enable_persistence as enable_global_persistence, \
    disable_persistence as disable_global_persistence
from plum.process import ProcessState


def load_checkpoint(pid):
    return globals.get_persistence().load_checkpoint(pid)


def retry_from_last_checkpoint(process_class, pid):
    return process_class.retry(load_checkpoint(pid))

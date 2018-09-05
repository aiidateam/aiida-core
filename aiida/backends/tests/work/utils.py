# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import uuid
from aiida import work


def create_test_runner(with_communicator=False):
    prefix = 'aiidatest-{}'.format(uuid.uuid4())
    if with_communicator:
        rmq_config = work.rmq.get_rmq_config(prefix)
    else:
        rmq_config = None
    runner = work.Runner(
        poll_interval=0.,
        rmq_config=rmq_config,
        enable_persistence=False
    )
    work.set_runner(runner)
    return runner

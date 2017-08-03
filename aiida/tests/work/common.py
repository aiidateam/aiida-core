# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.work.process import Process



class DummyProcess(Process):
    """
    A Process that does nothing when it runs.
    """

    @classmethod
    def define(cls, spec):
        super(DummyProcess, cls).define(spec)
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self):
        pass


class BadOutput(Process):
    """
    A Process that emits an output that isn't part of the spec raising an
    exception.
    """

    @classmethod
    def define(cls, spec):
        super(BadOutput, cls).define(spec)
        spec.dynamic_output()

    def _run(self):
        self.out("bad_output", 5)

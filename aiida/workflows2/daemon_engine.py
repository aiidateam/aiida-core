# -*- coding: utf-8 -*-

import plum.execution_engine
import plum.parallel

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class DaemonEngine(plum.execution_engine.ExecutionEngine):
    def submit(self, process, inputs):
        pass

    def run(self, process, inputs):
        pass

    def get_process(self, pid):
        pass


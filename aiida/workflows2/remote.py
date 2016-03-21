# -*- coding: utf-8 -*-

from aiida.workflows2.process import Process

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class SubmitInputs(Process):
    @staticmethod
    def _init(spec):
        from aiida.orm.code import Code
        spec.add_input('code', type=Code)

    def _run(self):
        pass

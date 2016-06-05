# -*- coding: utf-8 -*-

from aiida.workflows2.process import Process
from aiida.workflows2.execution_engine import execution_engine
import aiida.workflows2.util as util

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


def async(proc, _attributes=None, *args, **kwargs):
    if util.is_workfunction(proc):
        kwargs['__async'] = True
        return proc(*args, **kwargs)
    elif issubclass(proc, Process):
        # No need to consider args as a Process can't deal with positional
        # arguments anyway
        return execution_engine.submit(proc(attributes=_attributes), inputs=kwargs)


def asyncd(proc, _attributes=None, *args, **kwargs):
    # For now no daemon implementation so just run locally
    return async(proc, _attributes, *args, **kwargs)

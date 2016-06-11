# -*- coding: utf-8 -*-

import aiida.workflows2.util as util
from aiida.workflows2.execution_engine import execution_engine
from aiida.workflows2.process import Process
import aiida.workflows2.defaults as defaults

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


def async(process_class, *args, **kwargs):
    if util.is_workfunction(process_class):
        kwargs['__async'] = True
        return process_class(*args, **kwargs)
    elif issubclass(process_class, Process):
        # No need to consider args as a Process can't deal with positional
        # arguments anyway
        return execution_engine.submit(process_class, inputs=kwargs)


def asyncd(process_class, _jobs_store=None, **kwargs):
    if _jobs_store is None:
        _jobs_store = defaults.storage
    proc = defaults.factory.create_process(process_class, inputs=kwargs)
    _jobs_store.save(proc)
    return proc.pid

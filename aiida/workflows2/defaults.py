# -*- coding: utf-8 -*-
from plum.engine.serial import SerialEngine
from aiida.workflows2.execution_engine import ExecutionEngine
from aiida.workflows2.process_factory import ProcessFactory
from plum.persistence.pickle_persistence import PicklePersistence
from aiida.workflows2.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


# Have globals that can be used by all of AiiDA
factory = ProcessFactory(store_provenance=True)
storage = PicklePersistence(factory, '/tmp/to_run')
registry = ProcessRegistry(storage)
#execution_engine = ExecutionEngine(
#    process_factory=factory, process_registry=registry)
execution_engine = SerialEngine(process_factory=factory,
                                process_registry=registry)

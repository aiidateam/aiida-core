# -*- coding: utf-8 -*-
from plum.engine.serial import SerialEngine
from aiida.workflows2.execution_engine import ExecutionEngine
from aiida.workflows2.process_factory import ProcessFactory
from plum.persistence.pickle_persistence import PicklePersistence
from aiida.workflows2.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


# Have globals that can be used by all of AiiDA
factory = ProcessFactory(store_provenance=True)
storage = PicklePersistence(
    factory,
    directory='/tmp/processes/running',
    finished_directory='/tmp/processes/finished',
    failed_directory='/tmp/processes/failed')
registry = ProcessRegistry(storage)
#execution_engine = ExecutionEngine(
#    process_factory=factory, process_registry=registry)
execution_engine = SerialEngine(process_factory=factory,
                                process_registry=registry)

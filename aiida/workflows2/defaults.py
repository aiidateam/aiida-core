# -*- coding: utf-8 -*-
import os.path
import aiida.common.setup as setup
from plum.engine.serial import SerialEngine
import plum.class_loader
from plum.engine.parallel import MultithreadedEngine
from aiida.workflows2.execution_engine import ExecutionEngine
from aiida.workflows2.class_loader import ClassLoader
from aiida.workflows2.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"

WORKFLOWS_DIR = os.path.expanduser(os.path.join(
    setup.AIIDA_CONFIG_FOLDER,
    setup.WORKFLOWS_SUBDIR))

# Have globals that can be used by all of AiiDA
class_loader = plum.class_loader.ClassLoader(ClassLoader())
registry = ProcessRegistry()
# execution_engine = MultithreadedEngine(process_factory=factory,
#                                        process_registry=registry)
execution_engine = SerialEngine()

import aiida.workflows2.persistence
storage = aiida.workflows2.persistence.Persistence(
    auto_persist=True,
    directory=os.path.join(WORKFLOWS_DIR, 'running'),
    finished_directory=os.path.join(WORKFLOWS_DIR, 'finished'),
    failed_directory=os.path.join(WORKFLOWS_DIR, 'failed'))
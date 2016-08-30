# -*- coding: utf-8 -*-
import os.path
import aiida.common.setup as setup
from plum.engine.serial import SerialEngine
import plum.class_loader
from plum.engine.parallel import MultithreadedEngine
from aiida.workflows2.class_loader import ClassLoader
from aiida.workflows2.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

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
    auto_persist=False,
    running_directory=os.path.join(WORKFLOWS_DIR, 'running'),
    finished_directory=os.path.join(WORKFLOWS_DIR, 'finished'),
    failed_directory=os.path.join(WORKFLOWS_DIR, 'failed'))
# -*- coding: utf-8 -*-
from plum.engine.serial import SerialEngine
import plum.class_loader
from plum.engine.parallel import MultithreadedEngine

import plum.in_memory_database
import plum.knowledge_provider
import plum.knowledge_base
from aiida.work.class_loader import ClassLoader
from aiida.work.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


_kb = plum.knowledge_base.KnowledgeBase()
#_kb.add_provider(
#    plum.in_memory_database.InMemoryDatabase(
#        retain_inputs=False, retain_outputs=False))
_kb.add_provider(ProcessRegistry())
plum.knowledge_provider.set_global_provider(_kb)

# Have globals that can be used by all of AiiDA
class_loader = plum.class_loader.ClassLoader(ClassLoader())
registry = _kb
parallel_engine = MultithreadedEngine()
serial_engine = SerialEngine()

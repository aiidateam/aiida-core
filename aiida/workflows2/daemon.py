# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import aiida.workflows2.defaults as defaults
from plum.engine.ticking import TickingEngine

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


def run_all_saved_processes(engine, registry):
    futures = []
    for cp in registry.load_all_checkpoints():
        futures.append(engine.run_from(cp))
    return futures


def tick_workflow_engine(registry=None):
    if registry is None:
        import aiida.workflows2.defaults
        registry = aiida.workflows2.defaults.registry

    engine = TickingEngine(defaults.factory, registry)
    run_all_saved_processes(engine, registry)
    return engine.tick()


if __name__ == "__main__":
    """
    A convenience method so that this module can be ran ticking the engine once.
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded

    if not is_dbenv_loaded():
        load_dbenv()

    tick_workflow_engine()

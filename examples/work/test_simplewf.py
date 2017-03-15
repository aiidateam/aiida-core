# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded


if not is_dbenv_loaded():
    load_dbenv()

from aiida.work.run import run, submit

from aiida.tutorial.simple_wf import SimpleWF
from aiida.orm.data.parameter import ParameterData


p = ParameterData(dict=dict(number=12))
p.store()
submit(SimpleWF, params=p)

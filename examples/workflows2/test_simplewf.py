
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm.data.simple import make_int
from aiida.workflows2.run import run, asyncd

from aiida.tutorial.simple_wf import SimpleWF
from aiida.orm.data.parameter import ParameterData


p = ParameterData(dict=dict(number=12))
p.store()
asyncd(SimpleWF, params=p)

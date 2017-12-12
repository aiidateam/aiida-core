import plum.rmq
from apricotpy import persistable
from . import rmq
from . import transport
from . import utils


def object_factory(loop, process_class, *args, **kwargs):
    from aiida.work.process import FunctionProcess

    if utils.is_workfunction(process_class):
        wf_class = FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return wf_class(inputs=inputs)
    else:
        return process_class(*args, **kwargs)


def loop_factory(*args, **kwargs):
    loop = plum.PersistableEventLoop()
    loop.set_object_factory(object_factory)

    return loop

from aiida.work import utils, transport
from plum.util import object_factory as plum_object_factory


def object_factory(loop, process_class, *args, **kwargs):
    from aiida.work.process import FunctionProcess

    if utils.is_workfunction(process_class):
        wf_class = FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return plum_object_factory(loop, wf_class, inputs=inputs)
    else:
        return plum_object_factory(loop, process_class, *args, **kwargs)


def loop_factory(*args, **kwargs):
    from plum.loop import BaseEventLoop

    loop = BaseEventLoop(*args, **kwargs)
    loop.set_object_factory(object_factory)
    loop.create(transport.TransportQueue)

    return loop


def add_message_emitters(loop):
    """
    Add message emitters to the loop
    :param loop: The event loop
    """

    from aiida.work.event import DbPollingEmitter
    from aiida.work.legacy.event import WorkflowEmitter

    loop.create(DbPollingEmitter)
    # loop.insert(WorkflowEmitter())
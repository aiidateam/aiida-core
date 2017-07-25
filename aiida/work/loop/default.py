from collections import namedtuple
from . import utils
from aiida.work.process import Process

ResultAndPid = namedtuple("ResultWithPid", ["result", "pid"])

_loop = None


def get_loop():
    global _loop
    if _loop is None:
        _loop = utils.loop_factory()
        utils.add_message_emitters(_loop)

    return _loop


def reset():
    global _loop
    if _loop is not None:
        _loop.close()
        _loop = None


def run(process_class, *args, **inputs):
    """
    Run a workfunction or process and return the result.

    :param process_class: The process class or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The result of the process
    """
    # Do this here so that it doesn't enter as an input to the process
    proc = enqueue(process_class, *args, **inputs)
    return get_loop().run_until_complete(proc)


def run_get_pid(process_class, *args, **inputs):
    proc = enqueue(process_class, *args, **inputs)
    return ResultAndPid(get_loop().run_until_complete(proc), proc.pid)


def enqueue(process_class, *args, **inputs):
    """
    Enqueue a workfunction or process and return the Process instance

    :param process_class: The process class or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The Process instance
    """
    kwargs = {}
    if inputs:
        kwargs['inputs'] = inputs

    return get_loop().create(process_class, *args, **kwargs)


def dequeue(process):
    return get_loop().remove(process)


def run_loop():
    """
    Run the event loop, running any enqueued Processes until there are no more
    callbacks
    """
    loop = get_loop()
    future = loop.create_future()

    # Set the future when all processes are done
    def check_for_processes(loop, subject, body):
        if not loop.objects(obj_type=Process):
            future.set_result('done')
            loop.messages().remove_listener(check_for_processes)

    # List for any object being removed
    loop.messages().add_listener(check_for_processes, "loop.object.*.removed")

    return loop.run_until_complete(future)

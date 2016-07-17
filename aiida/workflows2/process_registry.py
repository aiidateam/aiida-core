
import plum.persistence.pickle_persistence
import plum.process_registry
import plum.process
import plum.simple_registry
import plum.process_monitor
import aiida.common.exceptions as exceptions
from aiida.common.lang import override
from aiida.workflows2.util import ProcessStack
from aiida.orm import load_node


class ProcessRegistry(plum.process_registry.ProcessRegistry,
                      plum.process.ProcessListener):
    def __init__(self):
        self._simple_registry = plum.simple_registry.SimpleRegistry()

    @property
    def current_pid(self):
        return ProcessStack.top().pid

    @property
    def current_calc_node(self):
        return ProcessStack.top().calc

    def get_running_pids(self):
        return plum.process_monitor.monitor.get_pids()

    @override
    def get_running_process(self, pid):
        return self._simple_registry.get_running_process(pid)

    @override
    def is_finished(self, pid):
        import aiida.orm

        try:
            return self._simple_registry.is_finished(pid)
        except KeyError:
            pass

        try:
            node = aiida.orm.load_node(pid)
        except exceptions.NotExistent:
            return False
        else:
            try:
                return node.has_finished_ok() or node.has_failed()
            except AttributeError:
                pass
            try:
                return node.is_sealed
            except AttributeError:
                pass

        raise ValueError("Could not find a Process with id '{}'".format(pid))

    @override
    def get_output(self, pid, port):
        return self.get_outputs()[port]

    @override
    def get_outputs(self, pid):
        # Try getting them from processes that have run in this interpreter
        try:
            return self._simple_registry.get_outputs(pid)
        except KeyError:
            pass
        # Try getting them from the node in the database
        try:
            return load_node(pid).get_outputs_dict()
        except exceptions.NotExistent:
            raise ValueError(
                "Could not find a Process with id '{}'".format(pid))


import plum.persistence.pickle_persistence
import plum.process
import plum.process_database
import plum.simple_database
import plum.process_monitor
import aiida.common.exceptions as exceptions
from aiida.common.lang import override
from aiida.workflows2.util import ProcessStack
from aiida.orm import load_node


class ProcessRegistry(plum.simple_database.ProcessDatabase):
    def __init__(self):
        self._simple_database =\
            plum.simple_database.SimpleDatabase(retain_outputs=False)

    @property
    def current_pid(self):
        return ProcessStack.top().pid

    @property
    def current_calc_node(self):
        return ProcessStack.top().calc

    @override
    def get_active_process(self, pid):
        return self._simple_database.get_active_process(pid)

    @override
    def has_finished(self, pid):
        import aiida.orm

        try:
            return self._simple_database.has_finished(pid)
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
            return self._simple_database.get_outputs(pid)
        except (KeyError, RuntimeError):
            pass
        # Try getting them from the node in the database
        try:
            return load_node(pid).get_outputs_dict()
        except exceptions.NotExistent:
            raise ValueError(
                "Could not find a Process with id '{}'".format(pid))

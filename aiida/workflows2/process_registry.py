
import plum.process
import plum.knowledge_provider
import plum.in_memory_database
import plum.process_monitor
import aiida.common.exceptions as exceptions
from aiida.common.lang import override
from aiida.workflows2.util import ProcessStack
from aiida.orm import load_node


class ProcessRegistry(plum.knowledge_provider.KnowledgeProvider):
    """
    This class is a knowledge provider that uses the AiiDA database to answer
    questions related to processes.
    """
    @property
    def current_pid(self):
        return ProcessStack.top().pid

    @property
    def current_calc_node(self):
        return ProcessStack.top().calc

    @override
    def has_finished(self, pid):
        import aiida.orm

        try:
            node = aiida.orm.load_node(pid)
        except exceptions.NotExistent:
            raise plum.knowledge_provider.NotKnown(
                "Can't find node with pk '{}'".format(pid))
        else:
            try:
                return node.has_finished_ok() or node.has_failed()
            except AttributeError:
                pass
            try:
                return node.is_sealed
            except AttributeError:
                pass

        raise plum.knowledge_provider.NotKnown()

    @override
    def get_inputs(self, pid):
        try:
            return load_node(pid).get_inputs_dict()
        except exceptions.NotExistent:
            raise plum.knowledge_provider.NotKnown(
                "Can't find node with pk '{}'".format(pid))

    @override
    def get_outputs(self, pid):
        try:
            return load_node(pid).get_outputs_dict()
        except exceptions.NotExistent:
            raise plum.knowledge_provider.NotKnown(
                "Can't find node with pk '{}'".format(pid))

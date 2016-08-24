
import collections
from plum.persistence.pickle_persistence import PicklePersistence
from plum.process import Process
from aiida.orm import load_node
from aiida.common.lang import override
from aiida.workflows2.defaults import class_loader


class Persistence(PicklePersistence):
    @override
    def load_checkpoint_from_file(self, filepath):
        cp = super(Persistence, self).load_checkpoint_from_file(filepath)

        cp[Process.BundleKeys.INPUTS.value] =\
            self._load_nodes_from(Process.BundleKeys.INPUTS.value)

        cp.set_class_loader(class_loader)
        return cp

    def _convert_to_ids(self, nodes):
        from aiida.orm import Node

        input_ids = {}
        for label, node in nodes.iteritems():
            if node is None:
                continue
            elif isinstance(node, Node):
                if node.is_stored:
                    input_ids[label] = node.pk
                else:
                    # Try using the UUID, but there's probably no chance of
                    # being abel to recover the node from this if not stored
                    # (for the time being)
                    input_ids[label] = node.uuid
            elif isinstance(node, collections.Mapping):
                input_ids[label] = self._convert_to_ids(node)

        return input_ids

    def _load_nodes_from(self, pks_mapping):
        """
        Take a dictionary of of {label: pk} or nested dictionary i.e.
        {label: {label: pk}} and convert to the equivalent dictionary but
        with nodes instead of the ids.

        :param pks_mapping: The dictionary of node pks.
        :return: A dictionary with the loaded nodes.
        """
        nodes = {}
        for label, pk in pks_mapping.iteritems():
            if isinstance(pk, collections.Mapping):
                nodes[label] = self._load_nodes_from(pk)
            else:
                nodes[label] = load_node(pk=pk)
        return nodes

import plum.persistence.file_process_record
from aiida.workflows2.persistance.process_record import ProcessRecord
from aiida.orm import load_node
import getpass
import pickle


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class FileProcessRecord(plum.persistence.file_process_record.FileProcessRecord,
                        ProcessRecord):

    def __init__(self, process, inputs, _user=None, _id=None, parent=None):
        # We don't want to the superclass to try to pickle the input nodes so
        # instead give it the UUIDS
        self._input_nodes = inputs
        input_uuids = {label: inp.uuid for label, inp in inputs.iteritems()}
        super(FileProcessRecord, self).__init__(process, input_uuids, _id, parent)

        if _user:
            self._user = _user
        else:
            self._user = getpass.getuser()
        self._calc_node = process.current_calculation_node
        self._calc_node_uuid = self._calc_node.uuid

    @property
    def user(self):
        return self._user

    @property
    def calculation_node(self):
        if not self._calc_node:
            self._calc_node = load_node(self._calc_node_uuid)
        return self._calc_node

    @property
    def inputs(self):
        if not self._input_nodes:
            # Translate the UUIDs back into a actual data nodes
            self._input_nodes = {label: load_node(uuid) for label, uuid in self._inputs.iteritems()}
        return self._input_nodes

    def create_child(self, process, inputs):
        pid = self.generate_id()
        child = FileProcessRecord(process, inputs, _id=pid, parent=self)
        self._children[pid] = child
        return child

    def __getstate__(self):
        odict = self.__dict__.copy()
        # Don't save these, they will be lazily loaded later
        odict['_input_nodes'] = None
        odict['_calc_node'] = None
        return odict

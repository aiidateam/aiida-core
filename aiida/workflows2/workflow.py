# -*- coding: utf-8 -*-

import plum.workflow
from aiida.workflows2.process import Process
from aiida.orm import load_node


class Workflow(Process, plum.workflow.Workflow):
    """
    This class represents an AiiDA workflow which can be executed and will
    have full provenance saved in the database.
    """

    _CHILD_LABEL = '__label'
    _INPUT_BUFFER = '__input_buffer'
    _spec_type = plum.workflow.WorkflowSpec

    def _continue_from(self, record, exec_engine=None):
        """
        Restore the state of the class to how it would have been

        :param record: The record to continue from
        """
        # Set up the input buffer of values waiting to be used as inputs
        if self._INPUT_BUFFER in record.instance_state:
            self._input_buffer =\
                {link: load_node(uuid=uuid) for link, uuid in
                 record.instance_state[self._INPUT_BUFFER].iteritems()}

        if record.children:
            # Now continue all the children that were running
            for child_record in record.children.values():
                label = child_record.instance_state[self._CHILD_LABEL]
                self._process_instances[label].continue_from(child_record)
        else:
            self.run(record.inputs)

    def _create_child_record(self, child, inputs):
        # Find the child
        child_label = self._find_instance_label(child)
        assert child_label

        child_record = super(Workflow, self)._create_child_record(child, inputs)
        child_record.instance_state[self._CHILD_LABEL] = child_label
        return child_record

    def _find_instance_label(self, process):
        inst_label = None
        for label, proc in self._process_instances.iteritems():
            if proc is process:
                inst_label = label
                break
        return inst_label

    # Messages #####################################################
    def _on_value_buffered(self, link, value):
        super(Workflow, self)._on_value_buffered(link, value)

        state = self._process_record.instance_state.setdefault(
            self._INPUT_BUFFER, {})
        state[str(link)] = value
        self._process_record.save()

    def _on_value_consumed(self, link, value):
        super(Workflow, self)._on_value_consumed(link, value)

        state = self._process_record.instance_state[self._INPUT_BUFFER]
        state.pop(str(link))
        self._process_record.save()
    ################################################################

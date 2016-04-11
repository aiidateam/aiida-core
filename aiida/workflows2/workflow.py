# -*- coding: utf-8 -*-

import plum.workflow
import aiida.workflows2.util as util


class Workflow(plum.workflow.Workflow):
    """
    This class represents an AiiDA workflow which can be executed and will
    have full provenance saved in the database.
    """

    @classmethod
    def _from_record(cls, record):
        # for proc in record.
        pass

    def run(self, inputs=None, exec_engine=None):
        with util.ProcessStack(self) as stack:
            if len(stack) > 1 and not exec_engine:
                exec_engine = stack[-2]._get_exec_engine.push(self)

            super(Workflow, self).run(inputs, exec_engine)

    def load(self, record):
        assert(record.process_class == self.__class__.__name__)

    def _load_from_record(self, record):
        pass

    def _on_value_buffered(self, link, value):
        self._state_storage[str(link)]

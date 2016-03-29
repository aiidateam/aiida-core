# -*- coding: utf-8 -*-

import plum.workflow
import aiida.workflows2.util as util


class Workflow(plum.workflow.Workflow):
    """
    This class represents an AiiDA workflow which can be executed and will
    have full provenance saved in the database.
    """

    def run(self, exec_engine=None):
        with util.ProcessStack(self) as stack:
            if len(stack) > 1 and not exec_engine:
                exec_engine = stack[-2]._get_exec_engine.push(self)

            super(Workflow, self).run(exec_engine)

    def load(self, record):
        assert(record.process_class == cls.__name__)


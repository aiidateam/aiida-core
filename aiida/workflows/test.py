# -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from aiida.orm.workflow import Workflow



class WorkflowTestEmpty(Workflow):
    """
    Empty workflow, just for testing
    """

    def __init__(self, **kwargs):
        super(WorkflowTestEmpty, self).__init__(**kwargs)

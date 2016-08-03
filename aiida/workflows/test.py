# -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from aiida.orm.workflow import Workflow

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class WorkflowTestEmpty(Workflow):
    """
    Empty workflow, just for testing
    """

    def __init__(self, **kwargs):
        super(WorkflowTestEmpty, self).__init__(**kwargs)

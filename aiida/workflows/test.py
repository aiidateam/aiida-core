# -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from aiida.orm.workflow import Workflow

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"

class WorkflowTestEmpty(Workflow):
    """
    Empty workflow, just for testing
    """    
    def __init__(self,**kwargs):        
        super(WorkflowTestEmpty, self).__init__(**kwargs)
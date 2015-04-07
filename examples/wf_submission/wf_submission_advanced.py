#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Nicolas Mounet, Riccardo Sabatini"

def launch_ws():

    """
    To control the wf status use the command line 
    
    verdi workflow list pk
    
    """
            
    import aiida.orm.workflow as wf
    from aiida.workflows import wf_demo
    from aiida.common.datastructures import wf_states
    
    params = {}
    params['nmachine']=2

    w = wf_demo.SubWorkflowDemo()
    w.start()

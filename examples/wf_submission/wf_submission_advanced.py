#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


def launch_ws():
    """
    To control the wf status use the command line 
    
    verdi workflow list pk
    
    """

    import aiida.orm.workflow as wf
    from aiida.workflows import wf_demo
    from aiida.common.datastructures import wf_states

    params = {}
    params['nmachine'] = 2

    w = wf_demo.SubWorkflowDemo()
    w.start()

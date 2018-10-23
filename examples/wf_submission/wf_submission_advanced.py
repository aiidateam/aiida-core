#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
def launch_ws():
    """
    To control the wf status use the command line 
    
    verdi workflow list pk
    
    """
    from aiida.workflows import wf_demo

    params = dict()
    params['nmachine'] = 2

    w = wf_demo.SubWorkflowDemo()
    w.start()

if __name__ == '__main__':
    launch_ws()
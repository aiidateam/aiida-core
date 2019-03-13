# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
File to be executed by IPython in order to register the line magic %aiida

This file can be put into the startup folder in order to have the line
magic available at startup.
The start up folder is usually at ``.ipython/profile_default/startup/``
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

if __name__ == "__main__":

    try:
        import aiida
        del aiida
    except ImportError:
        pass
    else:
        import IPython
        # pylint: disable=ungrouped-imports
        from aiida.tools.ipython.ipython_magics import load_ipython_extension

        # Get the current Ipython session
        IPYSESSION = IPython.get_ipython()

        # Register the line magic
        load_ipython_extension(IPYSESSION)

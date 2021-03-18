# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
File to be executed by IPython in order to register the line magic %aiida

This file can be put into the startup folder in order to have the line
magic available at startup.
The start up folder is usually at ``.ipython/profile_default/startup/``
"""

# DOCUMENTATION MARKER
if __name__ == '__main__':

    try:
        import aiida
        del aiida
    except ImportError:
        # AiiDA is not installed in this Python environment
        pass
    else:
        from aiida.tools.ipython.ipython_magics import register_ipython_extension
        register_ipython_extension()

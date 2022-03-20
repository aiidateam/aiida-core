# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Expose the AiiDA CLI, for usage as `python -m aiida`"""
import sys

if __name__ == '__main__':
    from aiida.cmdline.commands.cmd_verdi import verdi
    sys.exit(verdi())

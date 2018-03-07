# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# Default interval in seconds between calls
# This is used both in the work.transports.TransportQueue and in the
# transport.Transport class
# (unless replaced in plugins, as it actually is the case for SSH and local)
DEFAULT_TRANSPORT_INTERVAL = 30.
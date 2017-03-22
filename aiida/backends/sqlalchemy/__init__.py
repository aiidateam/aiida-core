# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# The next two serve as 'global' variables, set in the load_dbenv
# call. They are properly reset upon forking.
engine =  None
scopedsessionclass = None

def get_scoped_session():
    """
    Return a scoped session (according to SQLAlchemy docs, 
    this returns always the same object within a thread, and
    a different object in a different thread.
    Moreover, since we update the scopedsessionclass upon
    forking, also forks have different session objects.
    """
    if scopedsessionclass is None:
        s = None
    else:
        s = scopedsessionclass()

    return s


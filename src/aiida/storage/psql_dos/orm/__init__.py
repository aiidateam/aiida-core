###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of ORM backend entities."""

import warnings

from sqlalchemy.exc import SAWarning

# The :meth:`sqlalchemy.orm.unitofwork.UOWTransaction.register_object` method emits a warning whenever an object is
# registered that is not part of the session. This can happen when the session is committed or flushed and an object
# inside the session contains a reference to another object, for example through a relationship, is not explicitly part
# of the session. If that referenced object is not already stored and persisted, it might get lost. On the other hand,
# if the object was already persisted before, there is no risk.
#
# This situation occurs a lot in AiiDA's code base. Prime example is when a new process is created. Typically the input
# nodes are either already stored, or stored first. As soon as they get stored, the session is committed and the session
# is reset by expiring all objects. Now, the input links are created from the input nodes to the process node, and at
# the end the process node is stored to commit and persist it with the links. It is at this point that Sqlalchemy
# realises that the input nodes are not explicitly part of the session.
#
# One direct solution would be to add the input nodes again to the session before committing the process node and the
# links. However, this code is part of the backend independent :mod:`aiida.orm` module and this is a backend-specific
# problem. This is also just one example and there are most likely other places in the code where the problem arises.
# Therefore, as a work around, the specific warning is ignored through a warrning filter.
warnings.filterwarnings(
    'ignore', category=SAWarning, message='Object of type .* not in session, .* operation along .* will not proceed'
)

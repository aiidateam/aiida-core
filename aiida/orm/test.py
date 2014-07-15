"""
Classes needed for tests.
Must be here because subclasses of 'Node' must be within aiida.orm
"""
from aiida.orm import Node

class myNodeWithFields(Node):
    # State can be updated even after storing
    _updatable_attributes = ('state',) 

from aida.djsite.main.models import Node as DjangoNode
from aida.exceptions import NotExistent

class Node(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.
    """
    def __init__(self,uuid=None):
        if uuid:
            
        self._djtable = DjangoNode()

    @property
    def djtable(self):
        return self._djtable

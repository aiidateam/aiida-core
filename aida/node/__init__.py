from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from aida.djsite.main.models import Node as DjangoNode
from aida.common.exceptions import NotExistent


class NodeEntity(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.
    """
    def __init__(self,uuid=None):
        if uuid is not None:
            try:
                self._tablerow = DjangoNode.objects.get(uuid=uuid)
                # I do not check for multiple entries found
            except DoesNotExist:
                raise NotExistent("No entry with the UUID {} found".format(
                    uuid))
        else:
            self._tablerow = DjangoNode.objects.create()
            # Check if here we already have a UUID

        
        
    @property
    def uuid(self):
        return self.tablerow.uuid
        
    @property
    def tablerow(self):
        return self._tablerow

if __name__ == '__main__':
    a = Node()
    print a.uuid

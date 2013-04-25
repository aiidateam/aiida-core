if __name__ == "__main__":
    from aida.djsite.settings import settings
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aida.djsite.settings.settings'

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction

from aida.djsite.main.models import Node as DjangoNode
from aida.common.exceptions import NotExistent, InternalError
from aida.djsite.utils import get_automatic_user
from aida.common.folders import RepositoryFolder, SandboxFolder

# Name to be used for the section
_section_name = 'node'

class Node(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.
    """
    def __init__(self,uuid=None):
        self._can_be_modified = False
        if uuid is not None:
            # If I am loading, I cannot modify it
            self._can_be_modified = False
            try:
                self._tablerow = DjangoNode.objects.get(uuid=uuid)
                # I do not check for multiple entries found
            except DoesNotExist:
                raise NotExistent("No entry with the UUID {} found".format(
                    uuid))
            self._temp_folder = None
        else:
            self._tablerow = DjangoNode.objects.create(user=get_automatic_user())
            self._can_be_modified = True
            self._temp_folder = SandboxFolder()
        self._repo_folder = RepositoryFolder(section=_section_name, uuid=self.uuid)
            

    @property
    def uuid(self):
        return unicode(self.tablerow.uuid)
        
    @property
    def tablerow(self):
        return self._tablerow

    @property
    def folder(self):
        return self._repo_folder

    def get_temp_folder(self):
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def save(self):
        if self._can_be_modified:
            
            # I save the corresponding django entry
            with transaction.commit_on_success():
                self.tablerow.save()
                # TODO: set also properties!
                self.folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)
            
            self._temp_folder = None            
            self._can_be_modified = False

    # Called only upon real object destruction from memory
    # I just try to remove junk, whenever possible
    def __del__(self):
        if self._temp_folder is not None:
            self._temp_folder.erase()

if __name__ == '__main__':
    a = Node()
    a.save()
    print a.uuid

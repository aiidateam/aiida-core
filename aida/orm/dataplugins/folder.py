import os

from aida.orm import Data
from aida.common.exceptions import ModificationNotAllowed

class FolderData(Data):
    """
    Stores a folder with subfolders and files.

    No special attributes are set.
    """
    _plugin_type_string = ".".join([Data._plugin_type_string,'folder'])

    def __init__(self,**kwargs):
        super(FolderData,self).__init__(**kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            # TODO: check that there are no further args;
            # do the same in other classes
            return

    def replace_with_folder(self,folder,overwrite=True):
        """
        Replace the data with another folder, always copying and not moving the
        original files.

        Args:
            folder: the folder to copy from
            overwrite: if to overwrite the current content or not
        """

        if not os.path.isabs(folder):
            raise ValueError("folder must be an absolute path")

        # TODO: implement the logic on the folder? Or set a 'locked' flag on folders?

        if self._to_be_stored:
            self.path_subfolder.replace_with_folder(folder,move=False,overwrite=overwrite)
        else:
            raise ModificationNotAllowed("You cannot change the files after the node has been stored")

    

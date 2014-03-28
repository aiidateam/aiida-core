from aiida.orm import Data


class RemoteData(Data):
    """
    Store a link to a file or folder on a remote machine
    """
    def get_remote_machine(self):
        return self.get_attr('remote_machine')

    def set_remote_machine(self,val):
        self.set_attr('remote_machine', val)

    def get_remote_path(self):
        return self.get_attr('remote_path')

    def set_remote_path(self,val):
        self.set_attr('remote_path', val)

    def add_path(self,src_abs,dst_filename=None):
        """
        Disable adding files or directories to a RemoteData
        """
        from aiida.common.exceptions import ModificationNotAllowed
        raise ModificationNotAllowed("Cannot add files or directories to a RemoteData object")

    def validate(self):
        from aiida.common.exceptions import ValidationError

        super(RemoteData,self).validate()
        
        try:
            self.get_remote_path()
        except AttributeError:
            raise ValidationError("attribute 'remote_path' not set.")

        try:
            self.get_remote_machine()
        except AttributeError:
            raise ValidationError("attribute 'remote_machine' not set.")
    

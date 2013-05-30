from aida.orm import Data


class RemoteData(Data):
    """
    Store a link to a file or folder on a remote machine
    """
    _plugin_type_string = ".".join([Data._plugin_type_string,'remote'])

    def __init__(self,filename=None,**kwargs):
        super(RemoteData,self).__init__(**kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            return

        remote_path = kwargs.pop('remote_path', None)
        if remote_path is not None:
            self.set_remote_path(remote_path)

        remote_machine = kwargs.pop('remote_machine', None)
        if remote_machine is not None:
            self.set_remote_machine(remote_machine)    

        if kwargs:
            raise ValueError("The following parameters were not understood: {}".format(
                kwargs.keys()))

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
        from aida.common.exceptions import ModificationNotAllowed
        raise ModificationNotAllowed("Cannot add files or directories to a RemoteData object")

    def validate(self):
        from aida.common.exceptions import ValidationError

        super(RemoteData,self).validate()
        
        try:
            self.get_remote_path()
        except AttributeError:
            raise ValidationError("attribute 'remote_path' not set.")

        try:
            self.get_remote_machine()
        except AttributeError:
            raise ValidationError("attribute 'remote_machine' not set.")
    

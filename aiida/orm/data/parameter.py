from aiida.orm import Data

class ParameterData(Data):
    """
    Pass as input in the init a dictionary, and it will get stored as internal
    attributes.

    Usual rules for attribute names apply (in particular, keys cannot start with
    an underscore). If this is the case, a ValueError will be raised.
    
    You can then change/delete/add more attributes before storing with the
    usual methods of aiida.orm.Node
    """
    def __init__(self,dictionary=None,**kwargs):
        super(ParameterData,self).__init__(**kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            return

        # I set the keys
        for k, v in dictionary.iteritems():
            self.set_attr(k, v)

    def add_path(self, *args, **kwargs):
        from aiida.common.exceptions import ModificationNotAllowed
        raise ModificationNotAllowed("Cannot add files or directories to a ParameterData object")

    #    def validate(self):
    #        # There should be nothing specific to check
    #        super(ParameterData,self).validate()

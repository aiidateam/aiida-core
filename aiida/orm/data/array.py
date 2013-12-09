from aiida.orm import Data

class ArrayData(Data):
    """
    Store a set of arrays on disk (rather than on the database) in an efficient
    way using numpy.save() (therefore, this class requires numpy to be 
    installed).
    
    Each array is stored within the Node folder as a different .npy file.
    """

    def __init__(self,dictionary=None,**kwargs):
        super(ArrayData,self).__init__(**kwargs)

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            return

    def delete_array(self, name):
        """
        Delete an array from the node. Can only be called before storing.
        
        :param name: The name of the array to delete from the node.
        """
        import numpy

        fname = '{}.npy'.format(name)
        if fname not in self.get_path_list():
            raise KeyError("Array with name '{}' not found in node pk={}".format(
                name, self.pk))
        
        # remove both file and attribute
        self.remove_path(fname)
        try:
            self.del_attr(name)
        except (KeyError, AttributeError):
            # Should not happen, but do not crash if for some reason the 
            # property was not set.
            pass
        
    def arraynames(self):     
        """
        Return a list of all arrays stored in the node, listing the files (and 
        not relying on the properties).
        """
        return [i[:-4] for i in self.get_path_list() if i.endswith('.npy')]

    def get_cached_shape(self, name):
        """
        Return the shape of an array from the value cached in the properties.
        
        :param name: The name of the array.
        """
        return tuple(self.get_attr(name))

    def iterarrays(self):
        """
        Iterator that returns tuples (name, array) for each array stored in the
        node.
        """
        for name in self.arraynames():
            yield (name, self.get_array(name))

    def get_array(self, name):
        """
        Return an array stored in the node
        
        :param name: The name of the array to return.
        """
        import numpy
        
        fname = '{}.npy'.format(name)
        if fname not in self.get_path_list():
            raise KeyError("Array with name '{}' not found in node pk={}".format(
                name, self.pk))
        
        array = numpy.load(self.get_abs_path(fname))
        return array
    
    
    def set_array(self, name, array):
        """
        Store a new numpy array inside the node. Possibly overwrite the array
        if it already existed.
        
        Internally, it stores a name.npy file in numpy format.
        
        :param name: The name of the array.
        :param array: The numpy array to store.
        """
        import re
        import tempfile
        
        import numpy
    
        if not(isinstance(array, numpy.ndarray)):
            raise TypeError("ArrayData can only store numpy arrays. Convert "
                            "the object to an array first")
        
        # Check if the name is valid
        if not(name) or re.sub('[0-9a-zA-Z_]', '', name):
            raise ValueError("The name assigned to the array ({}) is not valid,"
                             "it can only contain digits, letters or underscores")
                
        fname = "{}.npy".format(name)
        
        with tempfile.NamedTemporaryFile() as f:
            # Store in a temporary file, and then add to the node
            numpy.save(f, array)
            f.flush() # Important to flush here, otherwise the next copy command
                      # will just copy an empty file
            self.add_path(f.name, fname)
        
        # Mainly for convenience, for querying purposes (both stores the fact
        # that there is an array with that name, and its shape
        self.set_attr(name, list(array.shape))
    

    def validate(self):
        """
        Check if the list of .npy files stored inside the node and the 
        list of properties match. Just a name check, no check on the size
        since this would require to reload all arrays and this may take time
        and memory.
        """
        from aiida.common.exceptions import ValidationError
        files = self.arraynames()
        properties = self.attrs()
        if set(files) != set(properties):
            raise ValidationError("Mismatch of files and properties for ArrayData"
                                  "node (pk={}): {} vs. {}".format(self.pk,
                                        files, properties))
        super(ArrayData,self).validate()

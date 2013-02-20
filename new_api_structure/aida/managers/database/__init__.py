class Backend(object):
    """
    Properties:
    * type: #from which subclasses are derived
    * location
    * password
    * ... (see configuration of a backend in django)

    Methods:
    * the methods for the Data class are shown below (store_files, store_jsons)
    * probably we will also need some store_field method to store a field
      that exists in a schema-ful database - storing simply fields for
      schemaless DBs.
      Here we also probably need to define the issue of ForeignKeys.
    """
    def store_files():
        """
        Basic method to store a list of files.
        Will be called by the Data base class.
        
        To be implemented in the subclasses.
        """
        pass

    def store_jsons():
        """
        Basic method to store a list of jsons.
        Will be called by the Data base class.

        To be implemented in the subclasses.
        """
        pass

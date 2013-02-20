class Data(object):
    """
    This is the base class for data objects. The init will actually 
    load the appropriate subclass in the plugins folder, depending
    on the value of the 'type' field.

    Properties:
    * uuid
    * type_name # To identify the subclass to load
    * mdate, cdate
    * jsons = {}
    * files = []
    * extra field for further parameters

    Methods:
    The following set of methods is defined in the base class, beside
    those already defined below:
    * _add_json()
    * _del_json()
    * _list_jsons()
    * _get_json()
    * _add_file()
    * _del_file()
    * _list_files()
    * _get_file() # To decide if this returns the path, the url, 
                  # or the fileobject
    The above methods are called by the plugin classes without the need
    of reimplementing them; the plugin must instead take care of deciding
    what is saved as file, what as a json, and how these are managed
    (the idea is that files will always remain files on the disk, while
     jsons can be either stored as .json files, or possibly in a nosql
     DB, and should therefore not contain big file - while allowing for
     generic querying in the future)

    Other methods
    * attach_backend(b) # Sets the backend to be used for storage, b is a
                        # aida.database.Backend object. 
                        # Maybe the backend should always be attached in the
                        # __init__?
    
    * store()           # calls the backend store method on this object.
                        # if available, calls the self.validate() method
                        # first

    * get_url()         # get an aidaurl using the repository://protocol

    * __init__(backend=...,uuid=...) will load an existing object, without
                       uuid with create a new empty object in general, and
                       then you have to specify the type_name instead.

    For saving, the logic could be the one of Django:
    * if uuid is None, create a new object upon saving
    * if uuid is not None, overwrite the object with that UUID if it exists,
      otherwise either raise an Exception or just add a new entry? To decide
      [maybe with a flag? This depends on who generates the UUID: this class,
      or (probably better?) the backend itself?
    * possibly, have also a .copy() method that copies all the content, and
      resets the uuid to None so that a new instance is saved upon storing.
      See if we also want to have a special flag to keep track of the original
      version, for persistance purposes, + related attributes and methods
      (e.g. get_original())

    The idea could that while creating an object, this gets created in a
    Sandbox folder for files and in RAM for jsons, and then stored on the
    permanent repository upon calling the.store() method.
    Think to a clever way to copy files to a sandbox when an object is
    retrieved from the repository, e.g. copy to the local Sandbox only if
    it is modified or added, and upon storing if a file is in the 
    self.files list, but not in the Sandbox, take the original version
    from self.get_original().files or something similar.

    Example of usage:
    b = Backend(type = 'filesystem', location='/aida/repo/')
    d = Data(backend = b, type_name = 'upf', **kwargs)
    d.functional = 'LDA'
    d.element = 'C'
    d.store()  
    """
    def validate(self):
        """
        Check if the object in the present state is a valid object, ready
        to be stored (e.g.: if all required properties of a pseudo are set).

        Must be implemented by the plugin subclass. Can be absent if no
        validation is required, but in general it is better to have it.

        Raises an Exception (to be yet defined, probably a
        aida.entities.EntityValidationError inherited from
        aida.common.exceptions.ValidationError) if not valid.
        """
        pass

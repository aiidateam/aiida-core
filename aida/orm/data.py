from aida.orm import Node
'''
Specifications of the Data class:
Aiida Data objects are subclasses of Node and should have 

Multiple inheritance must be suppoted, i.e. Data should have methods for querying and
be able to inherit other library objects such as ASE for structures.

Architecture note:
The code plugin is responsible for converting a raw data object produced by code
to Aiida standard object format. The data object then validates itself according to its
method. This is done independently in order to allow cross-validation of plugins.

'''

class Data(Node):
    # IMPORTANT! define it here, and not in the __init__, otherwise the classmethod query()
    # will not filter correctly
    _plugin_type_string = "data"
    _updatable_attributes = tuple() 
        
    def __init__(self,**kwargs):
        self._logger = super(Data,self).logger.getChild('data')
        super(Data,self).__init__(**kwargs)

    def validate(self):
        '''
        Each datatype has functionality to validate itself according to a schema or 
        a procedure (e.g. see halst/schema python schema validation)
        ''' 
        return True
        
    def add_link_from(self,src,*args,**kwargs):
        from aida.orm.calculation import Calculation

        if len(self.get_inputs()) > 1:
            raise ValueError("At most one node can enter a data node")
            
        if not isinstance(src, Calculation):
            raise ValueError("Links entering a data object can only be of type calculation")
        
        return super(Data,self).add_link_from(src,*args, **kwargs)
    
  
    #    def store(self):
    #   '''
    #   Depending on type, data object will serialize itself into a fileset, and insert data into the db.
    #   This is defined in the data plugin. The API needs to be defined.
    #   '''
    #   NEVER CALL PASS! ALWAYS CALL THE SUPERCLASS STORE() METHOD
    
    
    def retrieve(self):
        #TODO
        '''
        Depending on type, data object will read from fileset and DB to recreate the Aiida object.
        This is defined in the data plugin.
        '''
        super(Data,self).retrieve()
    
    

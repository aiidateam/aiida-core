from aida.node import Node

'''
TBD: Code should be taken out of the Node hierarchy. Along with computer, 
it is a type of equipment used to perform the calculation.
We assume that the number of codes will be much smaller than data and calculations.
'''

class Code(Node):
    _plugin_type_string = "code"
    _updatable_attributes = tuple() 
    
    def __init__(self,*args,**kwargs):
        self._logger = super(Code,self).logger.getChild('code')
        super(Code,self).__init__(*args, **kwargs)
        # TODO here!

    def validate(self):
        # ALWAYS CALL THE SUPERCLASS VALIDATE METHOD!
        return super(Code,self).validate()
        
    def add_link_from(self,src,*args,**kwargs):
        raise ValueError("A code node cannot have any input nodes")

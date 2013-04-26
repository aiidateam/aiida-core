from aida.node import Node

class Calculation(Node):
    def __init__(self,*args,**kwargs):
        self._logger = super(Data,self).logger.getChild('calculation')
        super(Data,self).__init__(*args, **kwargs)
        # TODO here!

    def validate(self):
        # TODO
        return True
        
    def add_link_from(self,src,*args,**kwargs):
        from aida.node.data import Data
        from aida.node.code import Code
        
        if not isinstance(src,(Data, Code)):
            raise ValueError("Nodes entering in calculation can only be of type data or code")
        
        return super(Data,self).add_link_to(dest,*args, **kwargs)


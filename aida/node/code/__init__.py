from aida.node import Node

class Code(Node):
    def __init__(self,*args,**kwargs):
        self._logger = super(Data,self).logger.getChild('code')
        super(Data,self).__init__(*args, **kwargs)
        # TODO here!

    def validate(self):
        # TODO
        return True
        
    def add_link_from(self,src,*args,**kwargs):
        raise ValueError("A code node cannot have any input nodes")

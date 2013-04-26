from aida.node import Node

class Data(Node):
    def __init__(self,*args,**kwargs):
        self._logger = super(Data,self).logger.getChild('data')
        super(Data,self).__init__(*args, **kwargs)
        # TODO here!

    def validate(self):
        # TODO
        return True
        
    def add_link_from(self,src,*args,**kwargs):
        from aida.node.calculation import Calculation

        if len(self.get_inputs()) > 1:
            raise ValueError("At most one node can enter a data node")
            
        if not isinstance(src,Calculation):
            raise ValueError("Nodes entering in data can only be of type calculation")
        
        return super(Data,self).add_link_to(dest,*args, **kwargs)


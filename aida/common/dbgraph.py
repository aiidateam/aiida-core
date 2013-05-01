import aida.node

''' 
Graph Rules:

1. Each Data node must have zero or one source calculation
2. Each calculation node must have one or more data inputs
3. Each calculation must be linked to one and only one code
4. Each calculation must be linked to one and only one computer

5. A data node may contain multiple data nodes. This is nested hierarchy. 
If there is a link between a data and a caclulation, there must be a link 
between at least one sub-data and one sub-calculation.

Alternatively, all subdata must be linked to at least one sub-calculation.

This is a mess, delay this for now.



6. A calculation node may contain multiple calculation nodes. This is a workflow.

'''

def GraphCheck():
    if self.type == 'calculation':
        raise GraphError('Node {0} violates connection rules')
   
   
def SuperNodes():
    
    
    
    
    
    
    
    
from aida.node import Node

'''
Each calculation object should be defined by analogy of a function 
with a fixed set of labeled and declared inputs.

mystruc = Struc(...)
myinputparam = InputParam(...)
myjobparam = JobParam(...)
myupfA = UPF(...)
myupfB = UPF(...)

MyCalc = Calc({'struc': Struc(), 'upfA': UPF(),...})
This will define the abstract object with labeled input ports of defined type. 

MyCalc({'struc':mystruc, 'upfA':myupfA, ...})

Calculations can exist in the db as empty entities of state 'Abstract'.
Also Data can exist in the db with 'Abstract' state. This can be used to pre-define a workflow.

Calculation can only be submitted if all the data inputs are filled with concrete data objects.
It then changes status to 'Prepared' and so on.
Note: a calculation is set to 'retrieved' when all output nodes are validated and stored (TBD). 

When dealing with workflows g(f(A,B),C) = h(A,B,C)
however g(f(A,B=5),C) = h(A,C) since B is concrete.

To repeat an existing (static) workflow, take the set of calculation nodes, 
copy them and related data nodes and set everything to abstract. Then run throught the static workflow manager.
User can choose new data inputs.

A dynamic workflow is a script that creates calc and data on the fly. 
The script can be stored as an attribute of a previously generated workflow.
Here each calculation needs to be hashed in order to be reused on restarts.

NOTE: Need to include functionality of an observer method in calc or data plugins, to check the data 
while the calculation is running, to make sure that everything is going as planned, otherwise stop.

'''

class Calculation(Node):
    _plugin_type_string = "calculation"
    _updatable_attributes = tuple() 
    
    def __init__(self,*args,**kwargs):
        self._logger = super(Calculation,self).logger.getChild('calculation')
        super(Calculation,self).__init__(*args, **kwargs)
        # define labeled data input ports
        # TODO here!


    def validate(self):
        # TODO
        # Check that each of supplied data objects matches correct data type. 
        # Assume data objects are validated. It's the data plugin method's job.
        super(Calculation,self).validate()
        
        
    def add_link_from(self,src, *args, **kwargs):
        '''
        Add a link with a code as destination.
        You can use the parameters of the base Node class, in particular the label
        parameter to label the link.
        '''
        
        from aida.node.data import Data
        from aida.node.code import Code
        
        
        if not isinstance(src,(Data, Code)):
            raise ValueError("Nodes entering in calculation can only be of type data or code")
        
        return super(Calculation,self).add_link_from(src, *args, **kwargs)
    

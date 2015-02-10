=================================
Extracting data from the Database
=================================

In this section we will overview some of the tools provided by AiiDA by means of you can navigate through the data inside the AiiDA database.

Finding input and output nodes
++++++++++++++++++++++++++++++

Let's start with a reference node that you loaded from the database, for example the node with PK 17::

  n = load_node(17)

Now, we want to find the nodes which have a direct link to this node.
There are several methods to extract this information (for developers see all 
the methods and their docstring: ``get_outputs``, ``get_outputs_dict``, 
``get_inputdata_dict``, ``c.get_inputs`` and ``c.get_inputs_dict``).
The most practical way to access this information, especially when working on 
the ``verdi shell``, is by means of the ``inp`` and ``out`` methods.

The ``inp`` method is used to list and access the nodes with a direct link to 
``n`` in input.
The names of the input links can be printed by ``list(n.inp)`` or interactively
by ``n.inp. + TAB``.
As an example, suppose that ``n`` has an input ``KpointsData`` object under the linkname 
``kpoints``. The command::

  n.inp.kpoints
  
returns the ``KpointsData`` object.

Similar methods exists for the ``out`` method, which will display the names of 
links in output from ``n`` and can be used to access such output nodes.
Suppose that ``n`` has an output ``FolderData`` with linkname ``retrieved``, than
the command::

  n.out.retrieved
  
returns the FolderData object. 

.. note:: At variance with input, there can be more than one output
  objects with the same linkname (for example: a code object can be used by several 
  calculations always with the same linkname ``code``).
  As such, for every output linkname, we append the string ``_pk``, with the pk of 
  the output node. There is also a linkname without pk appended, which is 
  assigned to the oldest link. As an example, imagine that ``n`` is a code, which 
  is used by calculation #18 and #19, the linknames shown by ``n.out`` are::
  
    n.out.  >>
      * code
      * code_18
      * code_19
    
  The method ``n.out.code_18`` and ``n.out.code_19`` will return two different 
  calculation objects, and ``n.out.code`` will return the oldest (the reference 
  is the creation time) between calculation 
  18 and 19. If one calculation (say 18) exist only in output, there is then less
  ambiguity, and you are sure that the output of ``n.out.code`` coincides with
  ``n.out.code_18``. 
  




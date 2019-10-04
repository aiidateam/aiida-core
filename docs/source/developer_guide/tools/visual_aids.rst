Visual Aids
###########

This section is dedicated to tools that facilitate the generation of visual
aids for the different aspects of AiiDA (such as provenance graphs).


Graph Easy
----------

This software might be useful for producing simple provenance graphs in ascii
format (or some other formats as well).
The code can be downloaded from
`this site <https://metacpan.org/pod/release/SHLOMIF/Graph-Easy-0.76/bin/graph-easy>`_
and can be installed by untaring and following the instructions in the
INSTALL file.
The manual for the code is also available
`here <hhttp://bloodgate.com/perl/graph/manual>`_,
but it is a little difficult to follow.
For simple cases uses, it sufices to write and input file such as this:

.. literalinclude:: include/graph_input.txt

And then process it by running:

.. code-block:: python

    graph-easy input.txt

which will in turn produce the following output (that can be easily redirectioned
to a file if you prefer):

.. literalinclude:: include/graph_auto.txt


Although this graph is not as ordered as one should want, it might be easier to
generate it that way and then re-arrange it a bit:

.. literalinclude:: include/graph_modif.txt


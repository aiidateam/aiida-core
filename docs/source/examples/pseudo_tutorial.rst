.. _my-ref-to-pseudo-tutorial:

Pseudopotential families tutorial
=================================

As you might have seen in the previous ``PWscf`` tutorial, the procedure of 
attaching a pseudopotential file to each atomic species could be a bit tedious.
In many situations, you will not produce a different pseudopotential file 
for every calculation you do. 
More likely, when you start a project you will stick to a pseudopotential file 
for as long as possible. 
Moreover, in a high-throughput calculation, you will like to do calculation 
over several elements keeping the same functional.
That's also part of the reason why there are several projects 
(like `PSLibrary <http://qe-forge.org/gf/project/pslibrary/frs/>`_ 
or `GBRV <http://www.physics.rutgers.edu/gbrv/>`_ to name a few), 
that intend to develop a set of pseudopotentials 
that covers most of the periodic table for different functionals.

That's why we introduced the pseudopotential families. 
You can think at them as for a group of pseudopotentials 
that are useful to pack together.
Let's say for example that I want to create a family of LDA Ultrasoft pseudos.
As the first step, 
you need to get all the pseudopotential files in a single folder.
For your convenience, it is useful to use a common name for your files, 
for example with a structure like 'Element.a-short-description.UPF'.

The utility to upload a family of pseudopotentials is accessed through the 
``verdi``::

  verdi upf uploadfamily path/to/folder name_of_the_family "some description for your convenience"

With the optional flag ``--stop-if-existing``, that will stop if the md5 key 
of the file to upload is found equal to another already present in the database.
After the upload, which may take some seconds, the upffamily will be ready to 
be used.

Note finally, for a successful upload, it will be needed to use a unique name
for every upf family that you upload. Moreover, it is also needed that no more 
than one UPF exists for every element, otherwise the choice of a UPF file would
be ambiguous.


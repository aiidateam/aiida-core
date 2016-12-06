.. _my-ref-to-pseudo-tutorial:

Handling pseudopotentials
=========================

Introduction: Pseudopotential families
++++++++++++++++++++++++++++++++++++++

As you might have seen in the previous ``PWscf`` tutorial, the procedure of attaching a pseudopotential file to each atomic species could be a bit tedious. In many situations, you will not produce a different pseudopotential file for every calculation you do. More likely, when you start a project you will stick to a pseudopotential file for as long as possible. Moreover, in a high-throughput calculation, you will like to do calculation over several elements keeping the same functional. That's also part of the reason why there are several projects (like `PSLibrary <http://qe-forge.org/gf/project/pslibrary/frs/>`_ or `GBRV <http://www.physics.rutgers.edu/gbrv/>`_ to name a few), that intend to develop a set of pseudopotentials that covers most of the periodic table for different functionals.

That's why we added the *pseudopotential families*. Each family is a set of pseudopotentials that are grouped together in a special type of `AiiDA Group of nodes`. Within each family, at most one pseudopotential can be present for a given chemical element.

Of course, a pseudopotential family does not have to completely cover the periodic table (also because such pseudopotential sets do not exist). This means that you can create a pseudopotential family containing only the pseudopotentials for a few elements that you are interested in.

.. note ::
    In principle, you can group different kinds of pseudopotentials into the same family. It is your responsibility to group only those with the same type, or obtained using the same functionals, approximations and / or levels of theory.

Creating a pseudopotential family
+++++++++++++++++++++++++++++++++

Let's say for example that we want to create a family of LDA ultrasoft pseudopotentials. As the first step, you need to get all the pseudopotential files in a single folder. For your convenience, it is useful to use a common name for your files, for example with a structure like 'Element.a-short-description.UPF'.

The utility to upload a family of pseudopotentials is accessed via ``verdi``::

    verdi data upf uploadfamily path/to/folder name_of_the_family "some description for your convenience"

where ``path/to/folder`` is the path to the folder where you collected all the UPF files that you want to add to the AiiDA database and to the family with name ``name_of_the_family``, and the final parameter is a string that is set in the ``description`` field of the group.

.. note:: This command will first check the MD5 checksum of each file, and
  it will not create a new UPFData node if the pseudopotential is already 
  present in the DB. In this case, it will simply add that UpfData node
  to the group with name ``name_of_the_family``.

.. note:: if you add the optional flag ``--stop-if-existing``, 
  the code will stop (without creating any new UPFData node, nor creating a group)
  if at least one of the files in the folder is already found in the AiiDA DB.

After the upload (which may take some seconds, so please be patient) 
the upffamily will be ready to be used.

Note that if you pass as ``name_of_the_family`` a name that already exists,
the pseudopotentials in the folder will be added to the existing group. The
code will raise an error if you try to add two (different) pseudopotentials for
the same element.

Getting the list of existing families
+++++++++++++++++++++++++++++++++++++
If you want to know what are the pseudopotential families already existing in 
the DB, type::
   
   verdi data upf listfamilies

Add a ``-d`` (or ``--with-description``) flag if you want to read also the
description of the family.

You can also filter the groups to get only a list of those containing 
a set of given elements using the ``-e`` option. For instance, if you want
to get only the families containing the elements ``Ba``, ``Ti`` and ``O``, use::

   verdi data upf listfamilies -e Ba Ti O


For more help on the command line options, type::
   
   verdi data upf listfamilies -h


Manually loading pseudopotentials
+++++++++++++++++++++++++++++++++

If you do not want to use pseudopotentials from a family, it is also possible to load them manually (even if this is, in general, discouraged by us).

A possible way of doing it is the following: we start by creating a list of pseudopotential filenames that we need to use::

    raw_pseudos = [
       "Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF",
       "Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF",
       "O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF"]

(in this simple example, we expect the pseudopotentials to be in the same
folder of the script).
Then, we loop over the filenames and add them to the AiiDA database. The 
``get_or_create`` method checks if the pseudopotential is already in the
database (by checking its MD5 checksum) and either stores it, or just returns
the node already present in the database (the second value returned is a
boolean and tells us if the pseudo was already present or not).
We also store the returned nodes in a list (``pseudos_to_use``).

::

    UpfData = DataFactory('upf')
    pseudos_to_use = []

    for filename in raw_pseudos:
        absname = os.path.abspath(filename)
        pseudo, created = UpfData.get_or_create(absname,use_first=True)
        pseudos_to_use.append(pseudo)

As the last step, we make a loop over the pseudopotentials,
and attach its pseudopotential object to the calculation::

    for pseudo in pseudos_to_use:
        calc.use_pseudo(pseudo, kind=pseudo.element)

.. note:: when the pseudopotential is created, it is parsed and the elements
  to which it refers is stored in the database and can be accessed using the 
  ``pseudo.element`` property, as shown above.


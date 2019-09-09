.. _my-ref-to-pseudo-tutorial:

Introduction: Pseudopotential families
++++++++++++++++++++++++++++++++++++++

The procedure of attaching a pseudopotential file to each atomic species
can easily become tedious. In many situations, you will not produce a different
pseudopotential file for every calculation you perform; most likely, when you start a project
you will stick to a pseudopotential file that is adequate for what you need.
Furthermore, in a high-throughput calculation, you will like to do calculations
over several elements while keeping the same functional.
That is also part of the reason why there are several projects
(like the `PSLibrary <http://qe-forge.org/gf/project/pslibrary/frs/>`_
or `GBRV <http://www.physics.rutgers.edu/gbrv/>`_
to name a few), that intend to develop a set of pseudopotentials that covers most
of the periodic table for different functionals.

For this reason we introduced the concept of *pseudopotential families*.
Each family is a set of pseudopotentials that are grouped together in a special type of
`AiiDA Group of nodes`. Within each family, at most one pseudopotential
can be present for a given chemical element.

A pseudopotential family does not necessarily have to  cover the whole periodic table.
This means that you can create a pseudopotential family containing only the
pseudopotentials for a few elements that you are interested in.

.. note::
    In principle, you can group different kinds of pseudopotentials into the same family.
    It is your responsibility to group only those with the same type,
    or obtained using the same functionals, approximations and / or levels of theory.

Creating a pseudopotential family
+++++++++++++++++++++++++++++++++

.. note::
    The following commands are specific to the `Quantum ESPRESSO
    interface <https://github.com/aiidateam/aiida-quantumespresso/>`_.
    For interfaces to other codes, please refer to the respective plugin documentation.

In the following, we will create a pseudopotential family.
First, you need to collect the pseudopotential files which should go into the family in a
single folder -- we'll call it ``path/to/folder``. You can then add the family to
the AiiDA database with ``verdi``::

    verdi data upf uploadfamily path/to/folder name_of_the_family "some description for your convenience"

where ``name_of_the_family`` should be a unique name for the family,
and the final parameter is a string that is set in the ``description`` field of the group.

If the a pseudopotential family with the same ``name_of_the_family`` exists already,
the pseudopotentials in the folder will be added to the existing group.
The code will raise an error if you try to add two (different) pseudopotentials for the same element.

After the upload (which may take some seconds, so please be patient)
the pseudopotential family will be ready for use.

.. hint::
    If you upload pseudopotentials which are already present in your database,
    AiiDA will use the existing ``UPFData`` node instead of creating a duplicate one.
    You can use the optional flag ``--stop-if-existing`` to instead abort
    (without changing anything in the database) if an existing pseudopotential is found.


Getting the list of existing families
+++++++++++++++++++++++++++++++++++++
To see wich pseudopotential families already exist in the database, type
::

   verdi data upf listfamilies

Add a ``-d`` (or ``--with-description``) flag if you also want to read the description of each family.

You can also filter the groups to get only a list of those containing a given set of elements
using the ``-e`` option. For instance, if you want to get only the families containing the
elements ``Ba``, ``Ti`` and ``O``, use
::

   verdi data upf listfamilies -e Ba Ti O


For more information on the command line options, type
::

   verdi data upf listfamilies -h


Manually adding pseudopotentials
++++++++++++++++++++++++++++++++

If you do not want to use pseudopotentials from a family, it is also possible to manually
add them to the database (even though we discourage this in general).

A possible way of doing it is the following: we start by creating a list of
pseudopotential filenames that we need to use::

    raw_pseudos = [
       "Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF",
       "Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF",
       "O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF"]

In this simple example, we expect the pseudopotentials to be in the same folder
of the script. Then, we loop over the filenames and add them to the AiiDA database.
The ``get_or_create`` method checks if the pseudopotential is already in the database
and either stores it, or just returns the node already present in the database.
The second value returned is a boolean and tells us if the pseudopotential was
already present or not. We also store the returned nodes in a list (``pseudos_to_use``).

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

.. note::
    When the pseudopotential is created, it is parsed and the elements to which it refers is stored
    in the database and can be accessed using the ``pseudo.element`` property, as shown above.
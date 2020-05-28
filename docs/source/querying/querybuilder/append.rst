.. _QueryBuilderAppend:

Attributes and extras
^^^^^^^^^^^^^^^^^^^^^

You should know by now that you can define additional properties of nodes
in the *attributes* and the *extras* of a node.
There will be many cases where you will either want to filter or project on
those entities. The following example gives us a PwCalculation where the cutoff
for the wavefunctions has a value above 30.0 Ry::

    qb = QueryBuilder()
    qb.append(PwCalculation, project=['*'], tag='calc')
    qb.append(
        Dict,
        with_outgoing='calc',
        filters={'attributes.SYSTEM.ecutwfc':{'>':30.0}},
        project=[
            'attributes.SYSTEM.ecutwfc',
            'attributes.SYSTEM.ecutrho',
        ]
    )

The above examples filters by a certain attribute.
Notice how you expand into the dictionary using the dot (.).
That works the same for the extras.

.. note::
    Comparisons in the attributes (extras) are also implicitly done by type.

Filtering or projecting on lists works similar to dictionaries.
You expand into the list using the dot (.) and afterwards adding the list-index.
The example below filters KpointsData by the first index in the mesh of KpointsData=instance, and returns that same index in the list::

    qb = QueryBuilder()
    qb.append(
        DataFactory('array.kpoints'),
        project=['attributes.mesh.0'],
        filters={'attributes.mesh.0':{'>':2}}
    )

Let's do a last example. You are familiar with the Quantum Espresso PWscf tutorial?
Great, because this will be our use case here. (If not, you can find it on the
`documentation of the aiida-quantumespresso package <http://aiida-quantumespresso.readthedocs.io/en/latest/user_guide/get_started/examples/pw_tutorial.html>`_.
We will query for calculations that were done on a certain structure (*mystructure*),
that fulfill certain requirements, such as a cutoff above 30.0.
In our case, we have a structure (an instance of StructureData) and an instance
of Dict that are both inputs to a PwCalculation.
You need to tell the QueryBuilder that::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        filters={'uuid':{'==':mystructure.uuid}},
        tag='strucure'
    )
    qb.append(
        PwCalculation,
        with_incoming='strucure',
        project=['*'],
        tag='calc'
    )
    qb.append(
        Dict,
        filters={'attributes.SYSTEM.ecutwfc':{'>':30.0}},
        with_outgoing='calc',
        tag='params'
    )

Cheats
++++++


A few cheats to save some typing:

*   The default edge specification, if no keyword is provided, is always
    *with_incoming* the previous vertice.
*   Equality filters ('==') can be shortened, as will be shown below.
*   Tags are not necessary, you can simply use the class as a label.
    This works as long as the same Aiida-class is not used again

A shorter version of the previous example::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        filters={'uuid':mystructure.uuid},
    )
    qb.append(
        PwCalculation,
        project='*',
    )
    qb.append(
        Dict,
        filters={'attributes.SYSTEM.ecutwfc':{'>':30.0}},
        with_outgoing=PwCalculation
    )


Advanced usage
++++++++++++++

Let's proceed to some more advanced stuff. If you've understood everything so far
you're in good shape to query the database, so you can skip the rest if you want.

.. ~
.. ~ Let's get the id  ``pk'' and the ORM-instances of all structures in the database::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(StructureData, project=['id', '*'])
.. ~     print list(qb.all())
.. ~
.. ~ This will return a list of result tuples, each one containing the pk and the corresponding
.. ~ StructureData instance.
.. ~ The following reverses the order inside the sublists::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(StructureData, project=['*', 'id'])
.. ~     print list(qb.all())
.. ~
.. ~ What if you want to project a certain attributes.
.. ~ That is trickier! You again need to tell the QueryBuilder the type.
.. ~ Assuming you want to get the energies returned by all PwCalculation done in the last 3 days::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             project=[{'attributes.energy':{'cast':'f'}}],
.. ~         )
.. ~     print list(qb.all())
.. ~
.. ~ You need to specify the type of the quantity, in that case a float:
.. ~
.. ~ *   'f' for floats
.. ~ *   'i' for integers
.. ~ *   't' for texts (strings, characters)
.. ~ *   'b' for booelans
.. ~ *   'd' for dates
.. ~
.. ~ So again, be consisted when storing values in the database.
.. ~ To sum up, a projection is technically a list of dictionaries.
.. ~ If you don't have to cast the type, because the value is not stored as an attribute (or extra),
.. ~ then the string is sufficient.
.. ~ If you don't care about the order (ensured by passing a list), you can also put values in
.. ~ one dictionary. Let's also get the units  of the energy::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             project={
.. ~                 'attributes.energy':{'cast':'f'},
.. ~                 'attributes.energy_units':{'cast':'t'},
.. ~             }
.. ~          )
.. ~     print list(qb.all())
.. ~
.. ~
.. ~ You can do much more with projections! You might be interested in the maximum value of an attribute
.. ~ among all results. This can be done much faster by the database than retrieving all results and
.. ~ doing it in Python. Let's get the maximum energy::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             project={
.. ~                 'attributes.energy':{'cast':'f', 'func':'max'},
.. ~             }
.. ~          )
.. ~     print list(qb.all())
.. ~
.. ~ The above query returns one row, the one with the maximum energy.
.. ~ Other functions implemented are:
.. ~
.. ~ *   *min*: get the row with the minimum value
.. ~ *   *count*: return the number of rows
.. ~
.. ~ To find out how many calculations resulted in energies above -5.0::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}},
.. ~             project={'id':{'func':'count'}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             filters={
.. ~                 'attributes.energy':{'>':-5.0},
.. ~             }
.. ~          )




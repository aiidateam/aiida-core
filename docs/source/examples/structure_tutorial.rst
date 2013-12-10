StructureData tutorial
======================

.. toctree::
   :maxdepth: 2

General comments
----------------

This section contains an example of how you can use the StructureData object to create complex crystals.
The main difference with ASE lies in the ase.Atom object.
It is implemented the possibility to have alloys or vacancies in a structure (although one must check whether the code one's using can support them).

Take a look at the following example::

  alat = 4. # angstrom
  cell = [[alat, 0., 0.,],
          [0., alat, 0.,],
          [0., 0., alat,],
         ]
  s = StructureData(cell=cell)
  s.append_atom(position=(0.,0.,0.),symbols=['Ba','Ca'],weights=[0.9,0.1])

The structure created has a cubic unit cell, and an occupancy site located at the origin. 
The parameters ``symbols``, ``weights`` and ``masses`` can be assigned as a float if no partial occupancy are desired, or as list, if one needs to specify the occupancy.
The length of these three input lists must be the same among all of them.
Weights identifies the percentual occupancy of the site: its sum must be a number from zero to one.
If it goes to one, and there are more than one chemical element on the site, the structure is an alloy (verified by ``s.is_alloy()``).

Finally, there is the possibility to have vacancies, whenever the total occupancy of at least one site doesn't reach one, as it could be in the following example::

  s.append_atom(position=(0.,0.,0.),symbols='Ca',weights=0.9)

The method to check whether there are vacancies is ``s.has_vancancies()``.
Vacancies and alloys can of course coexist.

Note that ASE doesn't support explicitely vacancies or alloys. When we deal with a simple structure, the correspondence between ASE and AiiDA structures is almost a one-to-one.
If there are vacancies or alloys, this correspondance cannot be done trivially and needs a manual intervention of the user.



Tutorial
--------

TO BE DONE   


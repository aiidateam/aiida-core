Dos
+++

Description
-----------
Use the plugin to support inputs of Quantum Espresso dos.x executable. Computes the
Density of states, and integrated charge density for a PW calculation.
See the projwfc doc see the QE `documentation`_ for more details.

.. _documentation: http://www.quantum-espresso.org/wp-content/uploads/Doc/INPUT_DOS.html

Supported codes
---------------
* tested from dos.x v.5.1.2 onwards

Inputs
------
* **parent_calculation**, A PW calculation. It is also recommended that a bands calculation be used as the parent
  for the best viewing results, though this is not mandatory.

* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of dos.x, as a nested dictionary, mapping the input of QE.
  See the QE documentation for the full list of variables and their meaning.


Outputs
-------
There are several output nodes that can be created by the plugin.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  (accessed by ``calculation.res``) Contains the wall time of the run, as well as any warnings that may occurred.

* output_dos :py:class:`XyData <aiida.orm.data.array.xy.XyData>`
  Contains the dos. The energy axis and dos can be found using::

    Dos.get_x()
    Dos.get_y()

  Which will return the tuples (in order)::

    [(u'Energy', Energy_array, 'eV')]
    [(u'integrated_dos', integrated_dos_array, 'states'),
     (u'dos', dos_array, 'states/eV')]

  Where the Energy_array is a numpy array given the energy values and the Dos_array is a numpy array giving the Dos values for each energy in the Energy_array. The
  integrated_dos_array returns the integral of the Dos_array from Emin to the given energy in the Energy_array.

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible
with the ``verdi calculation logshow`` command).
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.




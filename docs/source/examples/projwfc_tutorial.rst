.. _my-ref-to-projwfc-tutorial:

Projwfc
=======

.. note:: The Quantum Espresso Projwfc plugin referenced below is available in
          the EPFL version.

.. toctree::
   :maxdepth: 2


This chapter will show how to launch a single Projwfc (``projwfc.x``) calculation. It assumes you already familiar with the underlying code as well
as how to use basic features of AiiDA. This tutorial assumes you are at least familiar with the concepts introduced during the :ref:`my-ref-to-ph-tutorial`, specifically you should be familiar with using a parent calculation.

This section is intentially left short, as there is really nothing new in using projwfc calculations relative to ph calculations. Simply adapt the
script below to suit your needs, refer to the quantum espresso documentation.

Script to execute
-----------------

This is the script described in the tutorial above. You can use it, just
remember to customize it using the right parent_id,
the code, and the proper scheduler info.

::

    #!/usr/bin/env python
    from aiida import load_dbenv
    load_dbenv()

    from aiida.orm import Code
    from aiida.orm import CalculationFactory, DataFactory

    #####################
    # ADAPT TO YOUR NEEDS
    parent_id = 6
    codename = 'my-projwfc.x'
    #####################

    code = Code.get_from_string(codename)

    ParameterData = DataFactory('parameter')
    parameters = ParameterData(dict={
        'PROJWFC': {
            'DeltaE' : 0.2,
            'ngauss' : 1,
            'degauss' : 0.02
        }})

    QEPwCalc = CalculationFactory('quantumespresso.projwfc')
    parentcalc = load_node(parent_id)

    calc = code.new_calc()
    calc.set_max_wallclock_seconds(30*60) # 30 min
    calc.set_resources({"num_machines": 1})

    calc.use_parameters(parameters)
    calc.use_code(code)
    calc.use_parent_calculation(parentcalc)

    calc.store_all()
    print "created calculation with PK={}".format(calc.pk)
    calc.submit()



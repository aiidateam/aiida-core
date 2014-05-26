################
AiiDA schedulers
################

.. _my-reference-to-scheduler:

Supported schedulers
++++++++++++++++++++

The list below describes the supported *schedulers*, i.e. the batch job
schedulers that manage the job queues and execution on any given computer.

PBSPro
------
The `PBSPro`_ scheduler is supported (and it has been tested with version 12.1).

All the main features are supported with this scheduler.

The JobResource class to be used when setting the job resources is the
:ref:`NodeNumberJobResource`

.. _PBSPro: http://www.pbsworks.com/Product.aspx?id=1

SLURM
-----

The `SLURM`_ scheduler is supported (and it has been tested with version 2.5.4).

All the main features are supported with this scheduler.

The JobResource class to be used when setting the job resources is the
:ref:`NodeNumberJobResource`

.. _SLURM: https://computing.llnl.gov/linux/slurm/

SGE
---
The `SGE`_ scheduler (Sun Grid Engine, now called Oracle Grid Engine)
is supported (and it has been tested with version GE 6.2u3),
together with some of the main variants/forks.

All the main features are supported with this scheduler.

The JobResource class to be used when setting the job resources is the
:ref:`ParEnvJobResource`

.. _SGE: http://www.oracle.com/us/products/tools/oracle-grid-engine-075549.html


PBS/Torque
----------
PBS/Torque is not fully supported yet, even if its support is one of our
top priorities. For the moment, you can try the PBSPro plugin, that *may*
also work PBS/Torque (even if there will probably be some small issues).

Job resources
+++++++++++++

When asking a scheduler to allocate some nodes/machines for a given job,
we have to specify some job resources (that typically include information as, 
for instance, the number of required nodes or the numbers of MPI processes
per node).

Unfortunately, the way of specifying this piece of information is different on
different clusters. Instead of having one only abstract class, we chose to 
adopt different subclasses, keeping in this way the specification of the
resources as similar as possible to what the user would do when writing 
a scheduler script. Note that only one subclass can be used, given a
specific scheduler.

The base class, from which all job resource subclasses inherit, is
:py:class:`aiida.scheduler.datastructures.JobResource`. All classes define
at least one method, :py:meth:`get_tot_num_mpiprocs() <aiida.scheduler.datastructures.JobResource.get_tot_num_mpiprocs()>`,
that returns the total number of MPI processes requested.

.. note:: to load a specific job resource subclass, you can load it manually
  by directly loading the correct class, e..g.::

    from aiida.scheduler.datastructures import NodeNumberJobResource
    
  However, in general, you will pass the fields to set directly to the 
  :py:meth:`set_resources() <aiida.orm.calculation.Calculation.set_resources()>` method
  of a :py:meth:`Calculation <aiida.orm.calculation.Calculation>` object. For instance::
  
     calc = Calculation(computer=...) # select here a given computer configured
                                      # in AiiDA
     
     # This assumes that the computer is configured to use a scheduler with
     # job resources of type NodeNumberJobResource
     calc.set_resources({"num_machines": 4, "num_mpiprocs_per_machine": 16})


.. _NodeNumberJobResource:

NodeNumberJobResource (PBS-like)
--------------------------------
This is the way of specifying the job resources in PBS and SLURM. The class is
:py:class:`aiida.scheduler.datastructures.NodeNumberJobResource`.

Once an instance of the class is obtained, 
you have the following fields that you can set:

* ``res.num_machines``: specify the number of machines (also called nodes) on 
  which the code should run
* ``res.num_mpiprocs_per_machine``: number of MPI processes
  to use on each machine
* ``res.tot_num_mpiprocs``: the total number of MPI processes that this job is
  requesting
  
Note that you need to specify only two among the three fields above, for
instance::

    res = NodeNumberJobResource()
    res.num_machines = 4
    res.num_mpiprocs_per_machine = 16

asks the scheduler to allocate 4 machines, with 16 MPI processes on
each machine.
This will automatically ask for a total of ``4*16=64`` total number of
MPI processes.

The same can be achieved passing the fields directly to the constructor::

    res = NodeNumberJobResource(num_machines=4, num_mpiprocs_per_machine=16)

or, even better, directly calling the :py:meth:`set_resources() <aiida.orm.calculation.Calculation.set_resources()>`
method of the :py:meth:`Calculation <aiida.orm.calculation.Calculation>` class
(assuming here that ``calc`` is your calculation object)::

    calc.set_resources({"num_machines": 4, "num_mpiprocs_per_machine": 16})

.. note:: If you specify all three fields (not recommended), make sure that they satisfy::

      res.num_machines * res.num_mpiprocs_per_machine = res.tot_num_mpiprocs
    
  Moreover, if you specify ``res.tot_num_mpiprocs``, make sure that this is a multiple
  of ``res.num_machines`` and/or ``res.num_mpiprocs_per_machine``. 

.. note:: When creating a new computer, you will be asked for a
  ``default_mpiprocs_per_machine``. If you specify it, then you can
  avoid to specify ``num_mpiprocs_per_machine`` when creating the
  resources for that computer, and the default number will be used.
  
  Of course, all the requirements between ``num_machines``,
  ``num_mpiprocs_per_machine`` and ``tot_num_mpiprocs`` still apply.

  Moreover, you can explicitly specify ``num_mpiprocs_per_machine`` if 
  you want to use a value different from the default one.


.. _ParEnvJobResource:

ParEnvJobResource (SGE-like)
----------------------------
In SGE and similar schedulers, one has to specify a *parallel environment* and
the *total number of CPUs* requested. The class is
:py:class:`aiida.scheduler.datastructures.ParEnvJobResource`.

Once an instance of the class is obtained, 
you have the following fields that you can set:

* ``res.parallel_env``: specify the parallel environment in which you want
  to run your job (a string)
* ``res.tot_num_mpiprocs``: the total number of MPI processes that this job is
  requesting

Remember to always specify both fields. No checks are done on the consistency
between the specified parallel environment and the total number of MPI processes
requested (for instance, some parallel environments may have been configured
by your cluster administrator to run on a single machine). It is your
responsibility to make sure that the information is valid, otherwise the 
submission will fail.
  
Some examples:

* setting the fields one by one::

   res = ParEnvJobResource()
   res.parallel_env = 'mpi'
   res.tot_num_mpiprocs = 64
  
* setting the fields directly in the class constructor::

   res = ParEnvJobResource(parallel_env='mpi', tot_num_mpiprocs=64)

* even better, directly calling the :py:meth:`set_resources() <aiida.orm.calculation.Calculation.set_resources()>`
  method of the :py:meth:`Calculation <aiida.orm.calculation.Calculation>` class
  (assuming here that ``calc`` is your calculation object)::

    calc.set_resources({"parallel_env": 'mpi', "tot_num_mpiprocs": 64})
  

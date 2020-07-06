.. _topics:schedulers:

====================
Batch Job Schedulers
====================

Batch job schedulers manage the job queues and execution on a compute resource.
AiiDA ships with plugins for a range of schedulers, and this section describes the interface of these plugins.

See :ref:`this how-to <how-to:plugin-codes:scheduler>` for adding support for custom schedulers.

PBSPro
------

The `PBSPro`_ scheduler is supported (tested: version 12.1).

All the main features are supported with this scheduler.

Use the :ref:`topics:schedulers:job_resources:node` when setting job resources.

.. _PBSPro: http://www.pbsworks.com/Product.aspx?id=1

SLURM
-----

The `SLURM`_ scheduler is supported (tested: version 2.5.4).

All the main features are supported with this scheduler.

Use the :ref:`topics:schedulers:job_resources:node` when setting job resources.

.. _SLURM: https://slurm.schedmd.com/

SGE
---

The `SGE`_ scheduler (Sun Grid Engine, now called Oracle Grid Engine) and some of its main variants/forks are supported (tested: version GE 6.2u3).

All the main features are supported with this scheduler.

Use the :ref:`topics:schedulers:job_resources:par` when setting job resources.

.. _SGE: https://en.wikipedia.org/wiki/Oracle_Grid_Engine

LSF
---

The IBM `LSF`_ scheduler is supported (tested: version 9.1.3 on the CERN `lxplus` cluster).

.. _LSF: https://www-01.ibm.com/support/knowledgecenter/SSETD4_9.1.3/lsf_welcome.html

Torque
------

`Torque`_ (based on OpenPBS) is supported (tested: version 2.4.16 from Ubuntu).

All the main features are supported with this scheduler.

Use the :ref:`topics:schedulers:job_resources:node` when setting job resources.

.. _Torque: http://www.adaptivecomputing.com/products/open-source/torque/



Direct execution (bypassing schedulers)
---------------------------------------

The ``direct`` scheduler plugin simply executes the command in a new bash shell, puts it in the background and checks for its process ID (PID) to determine when the execution is completed.

Its main purpose is debugging on the local machine.
Use a proper batch scheduler for any production calculations.

.. warning::

    Compared to a proper batch scheduler, direct execution mode is fragile.
    In particular:

    * There is no queueing, i.e. all calculations run in parallel.
    * PID numeration is reset during reboots.

.. warning::

    Do *not* use the direct scheduler for running on a supercomputer.
    The job will end up running on the login node (which is typically forbidden), and if your centre has multiple login nodes, AiiDA may get confused if subsequent SSH connections end up at a different login node (causing AiiDA to infer that the job has completed).

All the main features are supported with this scheduler.

Use the :ref:`topics:schedulers:job_resources:node` when setting job resources.


.. _topics:schedulers:job_resources:

Job resources
-------------

Unsurprisingly, different schedulers have different ways of specifying the resources for a job (such as the number of required nodes or the numbers of MPI processes per node).

In AiiDA, these differences are accounted for by subclasses of the |JobResource|  class.
The previous section lists which subclass to use with a given scheduler.

All subclasses define at least the :py:meth:`~aiida.schedulers.datastructures.JobResource.get_tot_num_mpiprocs` method that returns the total number of MPI processes requested but otherwise have slightly different interfaces described in the following.

.. note::

    You can manually load a `specific` |JobResource| subclass by directly importing it, e.g.

    .. code-block:: python

        from aiida.schedulers.datastructures import NodeNumberJobResource

    In practice, however, the appropriate class will be inferred from scheduler configured for the relevant AiiDA computer, and you can simply set the relevant fields in the ``metadata.options`` input dictionary of the |CalcJob|.

    For a scheduler with job resources of type |NodeNumberJobResource|, this could be:

    .. code-block:: python

        from aiida.orm import load_code

        inputs = {
            'code': load_code('somecode@localhost'),  # The configured code to be used, which also defines the computer
            'metadata': {
                'options': {
                    'resources', {'num_machines': 4, 'num_mpiprocs_per_machine': 16}
                }
            }
        }


.. _topics:schedulers:job_resources:node:

NodeNumberJobResource (PBS-like)
................................

The |NodeNumberJobResource| class is used for specifying job resources in PBS and SLURM.

The class has the following attributes:

* ``res.num_machines``: the number of machines (also called nodes) on which the code should run
* ``res.num_mpiprocs_per_machine``: number of MPI processes to use on each machine
* ``res.tot_num_mpiprocs``: the total number of MPI processes that this job requests
* ``res.num_cores_per_machine``: the number of cores to use on each machine
* ``res.num_cores_per_mpiproc``: the number of cores to run each MPI process on

You need to specify only two among the first three fields above, but they have to be defined upon construction.
We suggest using the first two, for instance:

.. code-block:: python

    res = NodeNumberJobResource(num_machines=4, num_mpiprocs_per_machine=16)

asks the scheduler to allocate 4 machines, with 16 MPI processes on each machine.
This will automatically ask for a total of ``4*16=64`` total number of MPI processes.

.. note::

    When creating a new computer, you will be asked for a ``default_mpiprocs_per_machine``.
    If specified, it will automatically be used as the default value for ``num_mpiprocs_per_machine`` whenever creating the resources for that computer.

.. note::

    If you prefer using ``res.tot_num_mpiprocs`` instead, make sure it is a multiple of ``res.num_machines`` and/or ``res.num_mpiprocs_per_machine``.

    The first three fields are related by the equation:

    .. code-block:: python

        res.num_machines * res.num_mpiprocs_per_machine = res.tot_num_mpiprocs


The ``num_cores_per_machine`` and ``num_cores_per_mpiproc`` fields are optional and must satisfy the equation:

.. code-block:: python

    res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine


.. note::

    In PBSPro, the ``num_mpiprocs_per_machine`` and ``num_cores_per_machine`` fields are used for mpiprocs and ppn respectively.

    In Torque, the ``num_mpiprocs_per_machine`` field is used for ppn unless the ``num_mpiprocs_per_machine`` is specified.

.. _topics:schedulers:job_resources:par:

ParEnvJobResource (SGE-like)
............................

The :py:class:`~aiida.schedulers.datastructures.ParEnvJobResource` class is used for specifying the resources of SGE and similar schedulers, which require specifying a *parallel environment* and the *total number of CPUs* requested.

The class has the following attributes:

* ``res.parallel_env``: the parallel environment in which you want to run your job (a string)
* ``res.tot_num_mpiprocs``: the total number of MPI processes that this job requests

Both attributes are required.
No checks are done on the consistency between the specified parallel environment and the total number of MPI processes requested (for instance, some parallel environments may have been configured by your cluster administrator to run on a single machine).
It is your responsibility to make sure that the information is valid, otherwise the submission will fail.

Setting the fields directly in the class constructor:

.. code-block:: python

    res = ParEnvJobResource(parallel_env='mpi', tot_num_mpiprocs=64)

And setting the fields using the ``metadata.options`` input dictionary of the |CalcJob|:

.. code-block:: python

    inputs = {
        'metadata': {
            'options': {
                resources', {'parallel_env': 'mpi', 'tot_num_mpiprocs': 64}
            }
        }
    }


.. |NodeNumberJobResource| replace:: :py:class:`~aiida.schedulers.datastructures.NodeNumberJobResource`
.. |JobResource| replace:: :py:class:`~aiida.schedulers.datastructures.JobResource`
.. |CalcJob| replace:: :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`

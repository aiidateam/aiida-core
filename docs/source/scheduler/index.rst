.. _my-reference-to-scheduler:

Supported schedulers
++++++++++++++++++++

The list below describes the supported *schedulers*, i.e. the batch job schedulers that manage the job queues and execution on any given computer.

PBSPro
------
The `PBSPro`_ scheduler is supported (and it has been tested with version 12.1).

All the main features are supported with this scheduler.

The :ref:`JobResource <job_resources>` class to be used when setting the job resources is the :ref:`NodeNumberJobResource`.

.. _PBSPro: http://www.pbsworks.com/Product.aspx?id=1

SLURM
-----

The `SLURM`_ scheduler is supported (and it has been tested with version 2.5.4).

All the main features are supported with this scheduler.

The :ref:`JobResource <job_resources>` class to be used when setting the job resources is the :ref:`NodeNumberJobResource`.

.. _SLURM: https://slurm.schedmd.com/

SGE
---

The `SGE`_ scheduler (Sun Grid Engine, now called Oracle Grid Engine)
is supported (and it has been tested with version GE 6.2u3),
together with some of the main variants/forks.

All the main features are supported with this scheduler.

The :ref:`JobResource <job_resources>` class to be used when setting the job resources is the :ref:`ParEnvJobResource`.

.. _SGE: https://en.wikipedia.org/wiki/Oracle_Grid_Engine

LSF
---

The IBM `LSF`_ scheduler is supported and has been tested with version 9.1.3
on the CERN `lxplus` cluster.

.. _LSF: https://www-01.ibm.com/support/knowledgecenter/SSETD4_9.1.3/lsf_welcome.html

Torque
------

`Torque`_ (based on OpenPBS) is supported (and it has been tested with Torque v.2.4.16 from Ubuntu).

All the main features are supported with this scheduler.

The :ref:`JobResource <job_resources>` class to be used when setting the job resources is the :ref:`NodeNumberJobResource`.

.. _Torque: http://www.adaptivecomputing.com/products/open-source/torque/



Direct execution (bypassing schedulers)
---------------------------------------

The direct scheduler, to be used mainly for debugging, is an implementation of a scheduler plugin that does not require a real scheduler installed, but instead directly executes a command, puts it in the background, and checks for its process ID (PID) to discover if the execution is completed.

.. warning::
    The direct execution mode is very fragile. Currently, it spawns a separate Bash shell to execute a job and track each shell by process ID (PID). This poses following problems:

    * PID numeration is reset during reboots;
    * PID numeration is different from machine to machine, thus direct execution is *not* possible in multi-machine clusters, redirecting each SSH login to a different node in round-robin fashion;
    * there is no real queueing, hence, all calculation started will be run in parallel.

.. warning::
    Direct execution bypasses schedulers, so it should be used with care in order not to disturb the functioning of machines.

All the main features are supported with this scheduler.

The :ref:`JobResource <job_resources>` class to be used when setting the job resources is the :ref:`NodeNumberJobResource`


.. _job_resources:

Job resources
+++++++++++++

When asking a scheduler to allocate some nodes/machines for a given job, we have to specify some job resources, such as the number of required nodes or the numbers of MPI processes per node.

Unfortunately, the way of specifying this information is different on different clusters. In AiiDA, this is implemented in different subclasses of the :py:class:`aiida.schedulers.datastructures.JobResource` class. The subclass that should be used is given by the scheduler, as described in the previous section.

The interfaces of these subclasses are not all exactly the same. Instead, specifying the resources is similar to writing a scheduler script.  All classes define at least one method, :meth:`get_tot_num_mpiprocs <aiida.schedulers.datastructures.JobResource.get_tot_num_mpiprocs>`, that returns the total number of MPI processes requested.

In the following, the different :class:`JobResource <aiida.schedulers.datastructures.JobResource>` subclasses are described:

.. contents ::
    :local:

.. note::
    you can manually load a `specific` :class:`JobResource <aiida.schedulers.datastructures.JobResource>` subclass by directly importing it, e..g.
    ::

        from aiida.schedulers.datastructures import NodeNumberJobResource

    However, in general, you will pass the fields to set directly in the ``metadata.options`` input dictionary of the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`.
    For instance::

        from aiida.orm import load_code

        # This example assumes that the computer is configured to use a scheduler with job resources of type :py:class:`~aiida.schedulers.datastructures.NodeNumberJobResource`
        inputs = {
            'code': load_code('somecode@localhost'),  # The configured code to be used, which also defines the computer
            'metadata': {
                'options': {
                    'resources', {'num_machines': 4, 'num_mpiprocs_per_machine': 16}
                }
            }
        }


.. _NodeNumberJobResource:

NodeNumberJobResource (PBS-like)
--------------------------------
This is the way of specifying the job resources in PBS and SLURM. The class is :py:class:`~aiida.schedulers.datastructures.NodeNumberJobResource`.

Once an instance of the class is obtained, you have the following fields that you can set:

* ``res.num_machines``: specify the number of machines (also called nodes) on which the code should run
* ``res.num_mpiprocs_per_machine``: number of MPI processes to use on each machine
* ``res.tot_num_mpiprocs``: the total number of MPI processes that this job is requesting
* ``res.num_cores_per_machine``: specify the number of cores to use on each machine
* ``res.num_cores_per_mpiproc``: specify the number of cores to run each MPI process

Note that you need to specify only two among the first three fields above, but they have to be defined upon construction, for instance::

    res = NodeNumberJobResource(num_machines=4, num_mpiprocs_per_machine=16)

asks the scheduler to allocate 4 machines, with 16 MPI processes on each machine. This will automatically ask for a total of ``4*16=64`` total number of MPI processes.

.. note::
    If you specify res.num_machines, res.num_mpiprocs_per_machine, and res.tot_num_mpiprocs fields (not recommended), make sure that they satisfy::

        res.num_machines * res.num_mpiprocs_per_machine = res.tot_num_mpiprocs

    Moreover, if you specify ``res.tot_num_mpiprocs``, make sure that this is a multiple of ``res.num_machines`` and/or ``res.num_mpiprocs_per_machine``.

.. note::
    When creating a new computer, you will be asked for a ``default_mpiprocs_per_machine``. If you specify it, then you can avoid to specify ``num_mpiprocs_per_machine`` when creating the resources for that computer, and the default number will be used.

    Of course, all the requirements between ``num_machines``, ``num_mpiprocs_per_machine`` and ``tot_num_mpiprocs`` still apply.

    Moreover, you can explicitly specify ``num_mpiprocs_per_machine`` if you want to use a value different from the default one.


The num_cores_per_machine and num_cores_per_mpiproc fields are optional. If you specify num_mpiprocs_per_machine and num_cores_per_machine fields, make sure that::

    res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine

If you want to specifiy single value in num_mpiprocs_per_machine and  num_cores_per_machine, please make sure that res.num_cores_per_machine is multiple of res.num_cores_per_mpiproc and/or res.num_mpiprocs_per_machine.

.. note::
    In PBSPro, the num_mpiprocs_per_machine and num_cores_per_machine fields are used for mpiprocs and ppn respectively.

.. note::
    In Torque, the num_mpiprocs_per_machine field is used for ppn unless the num_mpiprocs_per_machine is specified.

.. _ParEnvJobResource:

ParEnvJobResource (SGE-like)
----------------------------
In SGE and similar schedulers, one has to specify a *parallel environment* and the *total number of CPUs* requested. The class is :py:class:`~aiida.schedulers.datastructures.ParEnvJobResource`.

Once an instance of the class is obtained, you have the following fields that you can set:

* ``res.parallel_env``: specify the parallel environment in which you want to run your job (a string)
* ``res.tot_num_mpiprocs``: the total number of MPI processes that this job is requesting

Remember to always specify both fields. No checks are done on the consistency between the specified parallel environment and the total number of MPI processes requested (for instance, some parallel environments may have been configured by your cluster administrator to run on a single machine). It is your responsibility to make sure that the information is valid, otherwise the  submission will fail.

Some examples:

* setting the fields directly in the class constructor::

    res = ParEnvJobResource(parallel_env='mpi', tot_num_mpiprocs=64)

* even better, you will pass the fields to set directly in the ``metadata.options`` input dictionary of the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`.::

    inputs = {
        'metadata': {
            'options': {
                resources', {'parallel_env': 'mpi', 'tot_num_mpiprocs': 64}
            }
        }
    }

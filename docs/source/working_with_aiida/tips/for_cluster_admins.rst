.. _for_cluster_admins:

Tips for supercomputer cluster administrators
=============================================

Optimising the SLURM scheduler configuration
--------------------------------------------

If too many jobs are submitted at the same time to the queue,
SLURM might have troubles in dealing with the new submissions.

This might result in the ``sbatch`` command returning a time-out error, but
eventually the job might be scheduled anyway. In this situation, AiiDA will
not have any way to know that the job has actually been run and will try to
resubmit the job again in the same folder, which will probably result in
a wide range of different errors (see, e.g., the discussion `in this issue
<https://github.com/aiidateam/aiida-core/issues/3404>`_).

Here we report a few suggestions and tricks (text adapted by us) to improve the
configuration of SLURM, courtesy of Miguel Gila and Maxime Martinasso
(from the Swiss Supercomputing Center `CSCS <http://www.cscs.ch>`_).

    We found two main reasons for SLURM to be slow when submitting a job and
    potentially returning a timeout while the jobs is/will be scheduled:

    - If many jobs are completing at the same time (with a success or fail
      status) SLURM will try to accommodate them as soon as possible and will
      delay the schedule operation which can potentially timeout.
      Imagine the scenario of a(nother) user submitting a lot of quickly
      failing jobs in a ``for`` loop.
      So, your job is registered in SLURM but, because of the
      slow schedule operation (with SLURM giving higher priority to dealing
      with the failing jobs of the other user), ``sbatch`` returns a timeout.
      On the next schedule operation (periodically triggered by SLURM) the job
      will be actually scheduled but you will not get a job ID back as your
      ``sbatch`` command already returned with a timeout error earlier.
      To avoid this, one can add ``reduce_completing_frag`` to
      ``SchedulerParameters``: this should limit the time spent by SLURM to
      look at completing jobs;
    - If there are identical nodes that are part of several partitions, then
      this will slow down the schedule operation of SLURM. Best is to delete
      such partitions or change their state to disable.
      In particular we found a bug (now more or less fixed) in which, if you
      have a large partition covering *all* the nodes, any node in completing
      state will defer the scheduling of jobs in any other partition
      overlapping with the large one over that node. Given some of the
      workloads we run, this practically disabled the regular scheduling cycle.
      The backfill will continue to run, but it is a lot less reactive
      (order of minutes vs. seconds).

    Moreover:

    - Make sure user job submission scripts don't try running too many very
      short-lived tasks very quickly/at the same time: if this happens,
      ``slurmctld`` will become unresponsive for large periods of time.
      Basically what would happen is that the control daemon is busy placing
      and removing tasks, deferring legitimate RPCs. On a large system like
      Daint they will pile up, resulting in commands like ``squeue`` or
      ``sbatch`` to timeout.

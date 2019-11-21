AiiDA cookbook (useful code snippets)
=====================================

This cookbook is intended to be a collection of useful short scripts and
code snippets that may be useful in the everyday usage of AiiDA.
Please read carefully the notes (if any) before running the scripts!

Checking the queued jobs on a scheduler
---------------------------------------

If you want to know if which jobs are currently on the scheduler (e.g.
to dynamically decide on which computer to submit, or to delay submission, etc.)
you can use a modification of the following script::



    def get_scheduler_jobs(only_current_user=True):
        """
        Return a list of all current jobs in the scheduler.

        .. note:: an SSH connection is open and closed at every
            launch of this function.

        :param only_current_user: if True, filters by these
            considering only those of the current user (if this
            feature is supported by the scheduler plugin). Otherwise,
            if False show all jobs.
        """
        from aiida import orm

        computer = Computer.get(name='deneb')
        transport = computer.get_transport()
        scheduler = computer.get_scheduler()
        scheduler.set_transport(transport)

        # this opens the SSH connection, for SSH transports
        with transport:
            if only_current_user:
                remote_username = transport.whoami()
                all_jobs = scheduler.get_jobs(
                    user=remote_username,
                    as_dict=True)
            else:
                all_jobs = scheduler.get_jobs(
                    as_dict=True)

        return all_jobs

    if __name__ == "__main__":
        all_jobs = get_scheduler_jobs(only_current_user=False)
        user_jobs = get_scheduler_jobs(only_current_user=True)

        print("Current user has {} jobs out of {} in the scheduler".format(
            len(user_jobs), len(all_jobs)
        ))

        print ("Detailed (user's) job view:")
        for job_id, job_info in user_jobs.items():
            print ("Job ID: {}".format(job_id))
            for k, v in job_info.items():
                if k == "raw_data":
                    continue
                print("  {}: {}".format(k, v))
            print("")

Use ``verdi run`` to execute it::

  verdi run file_with_script.py

.. note:: Every time you call the function, an ssh connection
  is executed! So be careful and run this function
  sparsely, or your supercomputer centre might block your account.

  Another alternative if you want to call many times the function
  is to pass the transport as a parameter, and keep it open from the outside.

An example output would be::

    Current user has 5 jobs out of 1425 in the scheduler
    Detailed (user's) job view:
    Job ID: 1658497
      job_id: 1658497
      wallclock_time_seconds: 38052
      title: aiida-2324985
      num_machines: 4
      job_state: RUNNING
      queue_name: parallel
      num_mpiprocs: 64
      allocated_machines_raw: r02-node[17-18,53-54]
      submission_time: 2018-03-28 09:21:35
      job_owner: some_remote_username
      dispatch_time: 2018-03-28 09:21:35
      annotation: None
      requested_wallclock_time_seconds: 82800

    (...)

Getting an AuthInfo knowing the computer and the user
-----------------------------------------------------

If you have an ORM ``Computer`` and and ORM ``User``, the way to get
an ``AuthInfo`` object is the following::

    AuthInfo.objects.get(dbcomputer_id=computer.id, aiidauser_id=user.id)

This might be useful, for instance, to then get a transport to connect to the
computer.

Here is, as an example, an useful utility function::

    def get_authinfo_from_computername(computername):
        from aiida.orm import AuthInfo, User, Computer
        from aiida.manage.manager import get_manager
        manager = get_manager()
        profile = manager.get_profile()
        return AuthInfo.objects.get(
            dbcomputer_id=Computer.get(name=computername).id,
            aiidauser_id=User.get(email=profile.default_user).id
        )

that you can then use, for instance, as follows::

    authinfo = get_authinfo_from_computername('localhost')
    with authinfo.get_transport() as transport:
        print(transport.listdir())

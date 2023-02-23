.. _how-to:cookbook:

========
Cookbook
========

This how-to page collects useful short scripts and code snippets that may be useful in the everyday usage of AiiDA.


Checking the queued jobs on a scheduler
=======================================

If you want to know if which jobs are currently on the scheduler (e.g. to dynamically decide on which computer to submit, or to delay submission, etc.) you can use the following script as an example:

.. code-block:: python

    def get_scheduler_jobs(computer_label='localhost', only_current_user=True):
        """Return a list of all current jobs in the scheduler.

        .. note:: an SSH connection is open and closed at every launch of this function.

        :param computer_label: the label of the computer.
        :param only_current_user: if True, only retrieve jobs of the current default user.
            (if this feature is supported by the scheduler plugin). Otherwise show all jobs.
        """
        from aiida import orm

        computer = Computer.collection.get(label=computer_label)
        client = computer.get_client()

        # This opens the SSH connection, for SSH transports
        with client:
            if only_current_user:
                remote_username = client.whoami()
                all_jobs = client.get_jobs(user=remote_username, as_dict=True)
            else:
                all_jobs = client.get_jobs(as_dict=True)

        return all_jobs

    if __name__ == '__main__':
        all_jobs = get_scheduler_jobs(only_current_user=False)
        user_jobs = get_scheduler_jobs(only_current_user=True)

        print(f'Current user has {len(user_jobs)} jobs out of {len(all_jobs)} in the scheduler'
        print('Detailed job view:')

        for job_id, job_info in user_jobs.items():
            print(f'Job ID: {job_id}')
            for k, v in job_info.items():
                if k == 'raw_data':
                    continue
                print(f'  {k}: {v}')
            print('')

Use ``verdi run`` to execute it:

.. code-block:: console

    verdi run file_with_script.py

.. important::

    Every time you call the function, two SSH connections are opened!
    So be careful and run this function sparsely, or your supercomputer center might block your account.
    A possible work around to this limitation is to pass the transport as a parameter, and pass it in so that it can be reused.

An example output would be::

    Current user has 5 jobs out of 1425 in the scheduler
    Detailed job view:
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


Getting an ``AuthInfo`` knowing the computer and the user
=========================================================

To open a transport to a computer, you need the corresponding :class:`~aiida.orm.authinfos.AuthInfo` object, which contains the required information for a specific user.
Once you have the relevant :class:`~aiida.orm.computers.Computer` and :class:`~aiida.orm.users.User` collection, you can obtain as follows:

.. code-block:: python

    computer.get_authinfo(user)

Here is, as an example, a useful utility function:

.. code-block:: python

    def get_authinfo_from_computer_label(computer_label):
        from aiida.orm import load_computer, User
        computer = load_computer(computer_label)
        user = User.collection.get_default()
        return computer.get_authinfo(user)

that you can then use, for instance, as follows:

.. code-block:: python

    authinfo = get_authinfo_from_computer_label('localhost')
    with authinfo.get_transport() as transport:
        print(transport.listdir())

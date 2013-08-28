############################
Setup of computers and codes
############################

Before being able to run the first calculation, you need to setup at least one
computer and one code, as described below.

Remote computer requirements
++++++++++++++++++++++++++++

A computer in AiiDA denotes any computational resource (with a batch job
scheduler) on which you will run your calculations. Computers typically are
clusters or supercomputers.

Requirements for a computer are:

* It must run a Unix-like operating system
* The default shell must be ``bash``
* It should have a batch scheduler installed (see :doc:`here <../scheduler/index>`
  for a list of supported batch schedulers)
* It must be accessible from the machine that runs AiiDA using one of the 
  available transports (see below).
  
The first step is to choose the transport to connect to the computer. Typically,
you will want to use the SSH transport, apart from a few special cases where
SSH connection is not possible (e.g., because you cannot setup a password-less
connection to the computer). In this case, you can install AiiDA directly on
the remote cluster, and use the ``local`` transport (in this way, commands to 
submit the jobs are simply executed on the AiiDA machine, and files are simply
copied on the disk instead of opening an SFTP connection).

If you plan to use the ``local`` transport, you can skip to the next section.

If you plan to use the ``SSH`` transport, you have to configure a password-less
login from your user to the cluster. If you don't know how to do, google for
something like "passwordless login ssh". We will add a more detailed explanation
here in the future.

Once you are able to connect to your cluster using::

   ssh YOURUSERNAME@YOURCLUSTERADDRESS
   
without the need to type a password, you can proceed to setup the computer.

Computer setup and configuration
++++++++++++++++++++++++++++++++



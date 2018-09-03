.. _setup_code:

************
Setup a code
************

Once you have at least one computer configured, you can configure the codes.
In AiiDA, for full reproducibility of each calculation, we store each code in
the database, and attach to each calculation a given code. This has the further
advantage to make very easy to query for all calculations that were run with 
a given code (for instance because I am looking for phonon calculations, or
because I discovered that a specific version had a bug and I want to rerun 
the calculations).

In AiiDA, we distinguish two types of codes: **remote** codes and **local** codes,
where the distinction between the two is described here below.

Remote codes
------------
With remote codes we denote codes that are installed/compiled
on the remote computer. Indeed, this is very often the case for codes installed
in supercomputers for high-performance computing applications, because the
code is typically installed and optimized on the supercomputer.
  
In AiiDA, a remote code is identified by two mandatory pieces of information: 

* A computer on which the code is (that must be a previously configured computer);
* The absolute path of the code executable on the remote computer.

Local codes
-----------
With local codes we denote codes for which the code is not 
already present on the remote machine, and must be copied for every submission.
This is the case if you have for instance a small, machine-independent Python
script that you did not copy previously in all your clusters.
  
In AiiDA, a local code can be set up by specifying:
  
* A folder, containing all files to be copied over at every submission
* The name of executable file among the files inside the folder specified above
  
Setting up a code
-----------------

The::

  verdi code
  
command allows to manage codes in AiiDA.

To setup a new code, you execute::

  verdi code setup
  
and you will be guided through a process to setup your code.

   
.. tip:: The code will ask you a few pieces of information. At every prompt, you can
   type the ``?`` character and press ``<enter>`` to get a more detailed
   explanation of what is being asked. 
     
You will be asked for:

* **label**:  A label to refer to this code. Note: this label is not enforced
  to be unique. However, if you try to keep it unique, at least within
  the same computer, you can use it later
  to refer and use to your code. Otherwise, you need to remember its ID or UUID.

* **description**: A human-readable description of this code (for instance "Quantum
  Espresso v.5.0.2 with 5.0.3 patches, pw.x code, compiled with openmpi")

* **default input plugin**: A string that identifies the default input plugin to
  be used to generate new calculations to use with this code.
  This string has to be a valid string recognized by the ``CalculationFactory``
  function. To get the list of all available Calculation plugin strings,
  use the ``verdi calculation plugins`` command. Note: if you do not want to 
  specify a default input plugin, you can write the string "None", but this is
  strongly discouraged, because then you will not be able to use
  the ``.get_builder`` method of the ``Code`` object.
  
* **local**: either True (for local codes) or False (for remote
  codes). For the meaning of the distinction, see above. Depending
  on your choice, you will be asked for:
  
  * LOCAL CODES:

    * **Folder with the code**: The folder on your local computer in which there
      are the files to be stored in the AiiDA repository, and that will then be
      copied over to the remote computers for every submitted calculation.
      This must be an absolute path on your computer.
    * **Relative path of the executable**: The relative path of the executable
      file inside the folder entered in the previous step.
  
  * REMOTE CODES:
  
    * **Remote computer name**: The computer name as on which the code resides,
      as configured and stored in the AiiDA database
      
    * **Remote absolute path**: The (full) absolute path of the code executable
      on the remote machine
    
For any type of code, you will also be asked for:
    
* **Text to prepend to each command execution**: This is a multiline string,
     whose content will be prepended inside the submission script before the
     real execution of the job. It is your responsibility to write proper ``bash`` code!
     This is intended for code-dependent code, **like for instance loading the
     modules that are required for that specific executable to run**. 
     Example::

       module load intelmpi
       
     *Remember*
     *to end the input by pressing* ``<CTRL>+D``.

* **Text to append to each command execution**: This is a multiline string,
  whose content will be appended inside the submission script after the
  real execution of the job. It is your responsibility to write proper ``bash`` code!
  This is intended for code-dependent code. *Remember*
  *to end the input by pressing* ``<CTRL>+D``.

At the end, you will get a confirmation command, and also the ID of the code in the
database (the ``pk``, i.e. the principal key, and the ``uuid``).

.. note:: Codes are a subclass of the :py:class:`Node <aiida.orm.node.Node>` class,
   and as such you can attach any set of attributes to the code. These can
   be extremely useful for querying: for instance, you can attach the version
   of the code as an attribute, or the code family (for instance: "pw.x code of 
   Quantum Espresso") to later query for all runs done with a pw.x code and
   version more recent than 5.0.0, for instance.  However, in the
   present AiiDA version you cannot add attributes from the command line using
   ``verdi``, but you have to do it using Python code.

.. note:: You can change the label of a code by using the following command::

   verdi code relabel "ID" "new-label"
   
  (Without the quotation marks!) "ID" can either be the numeric ID (PK) of
  the code (preferentially), or possibly its label (or label@computername), 
  if this string uniquely identifies a code.

  You can also list all available codes (and their relative IDs) with::

   verdi code list
   
  The ``verdi code list`` accepts some flags to filter only codes on a 
  given computer, only codes using a specific plugin, etc.; use the ``-h``
  command line option to see the documentation of all possible options.

  You can then get the information of a specific code with::

   verdi code show "ID"
   
  Finally, to delete a code use::

   verdi code delete "ID"
   
  (only if it wasn't used by any calculation, otherwise an exception
  is raised) 
   
And now, you are ready to launch your calculations!

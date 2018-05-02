.. _quick_installation:

******************
Quick installation
******************

.. _PyPI: https://pypi.python.org/pypi/aiida
.. _pip: https://pypi.python.org/pypi/pip/

This section will install AiiDA in the fastest way possible, but will leave very little to customize and is not guaranteed to work flawlessly.
It is highly recommended to read the full instructions in the :ref:`installation section<install>`.
AiiDA is available through the python package index `PyPI`_ and can be installed with the python package manager `pip`_.
In a terminal, execute the following command:

.. code-block:: bash

    pip install aiida

This will install the ``aiida-core`` package along with the four base plugins:

    * ``aiida-ase``
    * ``aiida-codtools``
    * ``aiida-nwchem``
    * ``aiida-quantumespresso``

After successful installation AiiDA needs to be setup, which includes setting up a profile and creating a database
This can be accomplished semi-automatically through AiiDA's command line interface ``verdi``.
For maximum control and customizability one can use ``verdi setup``, which will be explained in greater detail in the :ref:`setup section<setup_aiida>`.
For a quick installation, AiiDA provides ``verdi quicksetup`` which will try to setup all requirements with sensible defaults

.. code-block:: bash

    verdi quicksetup

The ``verdi quicksetup`` command will guide you through the setup process through a series of prompts.
After completing all the prompts you should have a working installation of AiiDA.
You can verify that the installation was successful by running

.. code-block:: bash

    verdi profile list

This should list the profile that was just created by the quicksetup

.. code-block:: bash

    > quicksetup (DEFAULT) (DAEMON PROFILE)

If the quick installation fails at any point, please refer to the :ref:`full installation guide<install>` for more details or the :ref:`troubleshooting section<troubleshooting>`.
For additional configuration, please refer to the :ref:`configuration section<configure_aiida>`.
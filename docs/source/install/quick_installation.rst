.. _quick_installation:

******************
Quick installation
******************

Prerequisites
=============

.. toggle-header::
    :header: **Ubuntu**

    .. code-block:: bash

        sudo apt-get install git python2.7-dev python3-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client rabbitmq-server

    See :ref:`Ubuntu instructions<details_ubuntu>` for details.


.. toggle-header::
    :header: **MacOS X (Homebrew)**

    .. code-block:: bash

        brew install git python postgresql rabbitmq
        brew services start postgresql
        brew services start rabbitmq

    You also need to install ``pip`` and ``virtualenv``. See for example this page (untested):
    https://www.andreagrandi.it/2018/12/19/installing-python-and-virtualenv-on-osx/

    See :ref:`MacOS X (Homebrew) instructions<details_brew>` for details.

.. toggle-header::
    :header: **MacOS X (MacPorts)**

    .. code-block:: bash

        sudo port install git python postgresql96 postgresql96-server rabbitmq-server
        pg_ctl -D /usr/local/var/postgres start

    You also need to install ``pip`` and ``virtualenv``. See for example this page (untested):
    https://truongtx.me/2014/02/25/mac-os-install-python-pip-virtualenv-using-macports

    See :ref:`MacOS X (MacPorts) instructions<details_macports>` for details.

.. toggle-header::
    :header: **Gentoo Linux**

    .. code-block:: bash

        emerge -av git python postgresql rabbitmq-server
        rc-update add rabbitmq

    See :ref:`Gentoo Linux instructions<details_gentoo>` for details.

.. toggle-header::
    :header: **Windows Subsystem for Linux**

    .. code-block:: bash

        sudo apt-get install git python2.7-dev python3-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client
        sudo service postgresql start
        # install rabbitmq on windows

    See :ref:`WSL instructions<details_wsl>` for details.


.. _quick_install:

Installation
============

Create and activate a virtual environment:

.. code-block:: bash

    virtualenv ~/.virtualenvs/aiida
    source ~/.virtualenvs/aiida/bin/activate

Install the ``aiida-core`` python package:

.. code-block:: bash

    pip install aiida-core
    reentry scan

Set up your AiiDA profile:

.. code-block:: bash

    verdi quicksetup

Start the AiiDA daemon process:

.. code-block:: bash

    verdi daemon start

Check that all services are up and running:

.. code-block:: bash

    verdi status

     ✓ profile:     On profile quicksetup
     ✓ repository:  /repo/aiida_dev/quicksetup
     ✓ postgres:    Connected to aiida@localhost:5432
     ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
     ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

If you see all checkmarks, it is time to :ref:`get started<get_started>`!

If the quick installation fails at any point, please refer
to the :ref:`full installation guide<installation>` for more details
or the :ref:`troubleshooting section<troubleshooting>`.

For configuration of tab completion or using AiiDA in jupyter, see the :ref:`configuration instructions <configure_aiida>` before moving on.

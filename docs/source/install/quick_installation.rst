.. _quick_installation:

******************
Quick installation
******************

Prerequisites
=============

.. toggle-header::
    :header: **Ubuntu**
    
    .. code-block:: bash

        sudo apt-get install git python2.7-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client rabbitmq-server
        sudo reboot

    See :ref:`Ubuntu instructions<details_ubuntu>` for details.


.. toggle-header::
    :header: **MacOS X (Homebrew)**
    
    .. code-block:: bash

        brew install git python postgresql rabbitmq
        brew services start postgresql
        brew services start rabbitmq

    See :ref:`MacOS X (Homebrew) instructions<details_brew>` for details.

.. toggle-header::
    :header: **MacOS X (MacPorts)**
    
    .. code-block:: bash

        sudo port install git python postgresql96 postgresql96-server rabbitmq-server
        pg_ctl -D /usr/local/var/postgres start

    See :ref:`MacOS X (MacPorts) instructions<details_macports>` for details.

.. toggle-header::
    :header: **Gentoo Linux**
    
    .. code-block:: bash

        emerge -av git python postgresql rabbitmq-server
        rc-update add rabbitmq
        sudo reboot

    See :ref:`Gentoo Linux instructions<details_gentoo>` for details.

.. toggle-header::
    :header: **Windows Subsystem for Linux**
    
    .. code-block:: bash

        sudo apt-get install git python2.7-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client
        sudo service postgresql start
        # install rabbitmq on windows

    See :ref:`WSL instructions<details_wsl>` for details.


.. _quick_install:

Installation
============

Install the ``aiida`` python package:

.. code-block:: bash

    pip install --pre aiida

Set up your AiiDA profile:

.. code-block:: bash

    verdi quicksetup

After completing the setup, your newly created profile should show up in the list:

.. code-block:: bash

    verdi profile list

    Info: configuration folder: /path.to/.aiida
    Info: default profile is highlighted and marked by the * symbol
    * coding_day

To make sure all the required resources such as the database and RabbitMQ are up and running, you can run the following command:

.. code-block:: bash

    verdi status

     ✓ profile:     On profile django
     ✓ repository:  /repo/aiida_dev/django
     ✓ postgres:    Connected to aiida@localhost:5432
     ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
     ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

If everything is up and running, it is time to :ref:`get started<get_started>`!

If the quick installation failed at any point, please refer 
to the :ref:`full installation guide<installation>` for more details 
or the :ref:`troubleshooting section<troubleshooting>`.
For additional configuration, please refer to the :ref:`configuration section<configure_aiida>`.

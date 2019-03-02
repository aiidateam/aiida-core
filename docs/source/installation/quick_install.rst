.. _quick_install:

******************
Quick installation
******************

Prerequisites
=============

.. toggle-header::
    :header: **Ubuntu**
    
    .. code-block:: bash

        sudo apt-get install git python2.7-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client
        sudo reboot

    See :ref:`Ubuntu instructions<details_ubuntu>` for details.


.. toggle-header::
    :header: **MacOS X (Homebrew)**
    
    .. code-block:: bash

        brew install git python postgresql
        pg_ctl -D /usr/local/var/postgres start

    See :ref:`MacOS X (Homebrew) instructions<details_brew>` for details.

.. toggle-header::
    :header: **MacOS X (MacPorts)**
    
    .. code-block:: bash

        sudo port install git python postgresql96 postgresql96-server
        pg_ctl -D /usr/local/var/postgres start

    See :ref:`MacOS X (MacPorts) instructions<details_macports>` for details.

.. toggle-header::
    :header: **Gentoo Linux**
    
    .. code-block:: bash

        emerge -av git python postgresql
        sudo reboot

    See :ref:`Gentoo Linux instructions<details_gentoo>` for details.

.. toggle-header::
    :header: **Windows Subsystem for Linux**
    
    .. code-block:: bash

        sudo apt-get install git python2.7-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client
        sudo service postgresql start

    See :ref:`WSL instructions<details_wsl>` for details.


Installation
============

Install the ``aiida`` python package:

.. code-block:: bash

    pip install aiida

.. note:: 
    If you prefer the `conda package manager <https://docs.conda.io/en/latest/#>`_, use  ``conda install -c conda-forge aiida-core`` instead.
    At this time, most AiiDA *plugins* are only available through ``pip`` (and you can mix the two).
    
Set up your AiiDA profile:

.. code-block:: bash

    verdi quicksetup

After completing the setup, your newly created profile should show up in the list:

.. code-block:: bash

    $ verdi profile list
    Configuration folder: /home/username/.aiida
    > quicksetup (DEFAULT) (DAEMON PROFILE)

Time to :ref:`get started<get_started>`!

If you got stuck at any point, see
the :ref:`full installation guide<installation>` or the :ref:`troubleshooting section<troubleshooting>` for more details.

For further customizations, such as TAB completion for ``verdi``
commands, see the :ref:`configuration section<configure_aiida>`.

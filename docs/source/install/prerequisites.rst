.. _install_prerequisites:

*************
Prerequisites
*************

AiiDA is designed to run on `Unix <https://en.wikipedia.org/wiki/Unix>`_ operating systems and requires the following software:

* `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_ or
  `zsh <https://en.wikipedia.org/wiki/Z_shell>`_ (The shell)
* `python`_ >= 3.6 (The programming language used by AiiDA)
* `python3-pip`_ (Python 3 package manager)
* `postgresql`_ (Database software, version 9.4 or higher)
* `RabbitMQ`_ (A message broker necessary for AiiDA to communicate between processes)

Depending on your set up, there are a few optional dependencies:

* `virtualenv`_ (Software to create a virtual python environment to install AiiDA in)
* `virtualenvwrapper`_ (Wrapper for ``virtualenv`` to easily handle virtual environments)
* `graphviz`_ (For plotting AiiDA provenance graphs)
* `git`_ (Version control system used for AiiDA development)

.. _graphviz: https://www.graphviz.org/download
.. _git: https://git-scm.com/downloads
.. _python: https://www.python.org/downloads
.. _python3-pip: https://packaging.python.org/installing/#requirements-for-installing-packages
.. _virtualenv: https://packages.ubuntu.com/bionic/virtualenv
.. _virtualenvwrapper: https://packages.ubuntu.com/bionic/virtualenvwrapper
.. _postgresql: https://www.postgresql.org/downloads
.. _RabbitMQ: https://www.rabbitmq.com/


Supported operating systems
===========================

AiiDA has been tested on the following platforms:

* Ubuntu 14.04, 16.04, 18.04
* Mac OS X

We expect AiiDA to also run on:

* Older and newer Ubuntu versions
* Other Linux distributions
* Windows Subsystem for Linux (WSL)

Below, we provide installation instructions for a number of operating systems.

.. _details_ubuntu:

Ubuntu
======

To install the prerequisites on Ubuntu and any other Debian derived distribution, you can use the ``apt`` package manager.
The following will install the basic ``python`` requirements and the ``git`` source control manager:

.. code-block:: bash

    sudo apt-get install git python3-dev python3-pip virtualenv

To install the requirements for the ``postgres`` database run the following:

.. code-block:: bash

    sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

For a more detailed description of database requirements and usage see the :ref:`database<database>` section.

Finally, install the RabbitMQ message broker:

.. code-block:: bash

    sudo apt-get install rabbitmq-server

This installs and adds RabbitMQ as a system service. To check whether it is running:

.. code-block:: bash

    sudo rabbitmqctl status

If it is not running already, it should after a reboot.
For problems with installing RabbitMQ, refer to the detailed instructions provided on the `RabbitMQ website for Debian based distributions <https://www.rabbitmq.com/install-debian.html>`_.


.. _details_brew:

Mac OS X (homebrew)
===================

For Mac OS we recommend using the `Homebrew`_ package manager.
If you have not installed Homebrew yet, you can do so with the following command:

.. code-block:: bash

    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

.. _Homebrew: http://brew.sh/index_de.html

After you have installed Homebrew, you can install the basic requirements as follows:

.. code-block:: bash

    brew install git python postgresql

To start the ``postgres`` database server, execute:

.. code-block:: bash

    brew services start postgresql

For a more detailed description of database requirements and usage see the :ref:`database<database>` section.
Installing the RabbitMQ message broke through Homebrew is as easy as:

.. code-block:: bash

    brew install rabbitmq

To start the server and add it as a self-starting service, run:

.. code-block:: bash

    brew services start rabbitmq


You can check whether it is running by checking the status through the command:

.. code-block:: bash

    /usr/local/sbin/rabbitmqctl status

If you encounter problems installing RabbitMQ, please refer to the detailed instructions provided on the `website of RabbitMQ itself for Homebrew <https://www.rabbitmq.com/install-homebrew.html>`_.


.. _details_macports:

Mac OS X (MacPorts)
===================

.. _macports: https://www.macports.org/

Another package manager for MacOS is `macports`_.

.. code-block:: bash

    sudo port install git python postgresql96 postgresql96-server rabbitmq-server

To start the ``postgres`` database server, run:

.. code-block:: bash

    sudo su postgres
    pg_ctl -D /opt/local/var/db/postgresql96/defaultdb start

To start the ``rabbitmq`` server, run:

.. code-block:: bash

    sudo launchctl load -w /Library/LaunchDaemons/org.macports.rabbitmq-server.plist

You can check whether it is running as follows:

.. code-block:: bash

    sudo rabbitmqctl status
    # this starts ``rabbitmq`` at system startup:
    sudo port load rabbitmq-server

.. note::
    Be sure to install ``rabbitmq-server 3.7.9`` or later. If ``rabbitmqctl status`` returns an error "Hostname mismatch", the easiest solution
    can be to simply ``sudo port uninstall`` the package and install it again.


.. _details_gentoo:

Gentoo Linux
============

To install RabbitMQ on a Gentoo distribution through the ``portage`` package manager run the following command:

.. code-block:: bash

    emerge -av rabbitmq-server

To make sure that RabbitMQ is started at system boot, execute:

.. code-block:: bash

    rc-update add rabbitmq

If you want to manually start the RabbitMQ server you can use:

.. code-block:: bash

    /etc/init.d/rabbitmq start

Make sure that RabbitMQ is running with:

.. code-block:: bash

    rabbitmqctl status

.. note::
    If you have encounter the following error

    .. code-block:: bash

        Argument '-smp enable' not supported."

    Remove the mentioned option from the file ``/usr/libexec/rabbitmq/rabbitmq-env`` and restart the server.
    If you still have trouble getting RabbitMQ to run, please refer to the detailed instructions provided on the `website of RabbitMQ itself for generic Unix systems <https://www.rabbitmq.com/install-generic-unix.html>`_.


.. _details_wsl:

Windows Subsystem for Linux (Ubuntu)
====================================

The guide for Ubuntu above can generally be followed, but there are a few things to note:

.. hint::

    Installing `Ubuntu <https://www.microsoft.com/en-gb/p/ubuntu/9nblggh4msv6?source=lp&activetab=pivot:overviewtab>`_ instead of the version specific applications, will let you have the latest LTS version.

#. The `Windows native RabbitMQ <https://www.rabbitmq.com/install-windows.html>`_ should be installed and started.
   (For WSL 2, this should not be necessary.)

#. Linux services under WSL are not started automatically.
   To start the PostgreSQL and RabbitMQ-server services, type the commands below in the terminal::

     sudo service postgresql start
     sudo service rabbitmq-server start

   .. tip::

       These services may be run at startup *without* passing a password in the following way:

       Create a ``.sh`` file with the lines above, but *without* ``sudo``.
       Make the file executeable, i.e., type::

         chmod +x /path/to/file.sh

       Then type::

         sudo visudo

       And add the line::

         <username> ALL=(root) NOPASSWD: /path/to/file.sh

       Replacing ``<username>`` with your Ubuntu username.
       This will allow you to run *only* this specific ``.sh`` file with ``root`` access (without password), without lowering security on the rest of your system.

#. There is a `known issue <https://github.com/Microsoft/WSL/issues/856>`_ in WSL Ubuntu 18.04 where the timezone is not configured correctly out-of-the-box, which may cause problem for the database.
   The following command can be used to re-configure the time zone::

     sudo dpkg-reconfigure tzdata

#. The file open limit may need to be raised using ``ulimit -n 2048`` (default is 1024), when running tests.
   You can check the limit by using ``ulimit -n``.

   .. hint:: This may need to be run every time the system starts up.

It may be worth considering adding some of these commands to your ``~/.bashrc`` file, since some of these settings may reset upon reboot.

.. hint:: For using WSL as a developer, please see the considerations made in our `wiki-page for developers <https://github.com/aiidateam/aiida-core/wiki/Development-environment#using-windows-subsystem-for-linux-wsl>`_.

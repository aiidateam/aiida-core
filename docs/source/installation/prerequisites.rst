.. _install_prerequisites:

*************
Prerequisites
*************

AiiDA is designed to run on `Unix <https://en.wikipedia.org/wiki/Unix>`_ operating systems and requires the following software:

* `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_ or
  `zsh <https://en.wikipedia.org/wiki/Z_shell>`_ (The shell)
* `python-2.7.x`_ (The programming language used by AiiDA)
* `python-pip`_ (Python package manager)
* `postgresql`_ (Database software, version 9.4 or higher)

Depending on your set up, there are a few optional dependencies:

* `virtualenv`_ (Software to create a virtual python environment to install AiiDA in)
* `graphviz`_ (For plotting AiiDA provenance graphs)
* `git`_ (Version control system used for AiiDA development)

.. _graphviz: https://www.graphviz.org/download 
.. _git: https://git-scm.com/downloads
.. _python-2.7.x: https://www.python.org/downloads
.. _python-pip: https://packaging.python.org/installing/#requirements-for-installing-packages
.. _virtualenv: https://packages.ubuntu.com/xenial/virtualenv
.. _postgresql: https://www.postgresql.org/downloads


Supported operating systems
===========================

AiiDA has been tested on the following platforms:

* Ubuntu 14.04, 16.04
* Mac OS X

We expect AiiDA to also run on:

* Older and newer Ubuntu versions
* Other Linux distributions
* Windows subsystem for Linux

Below, we provide installation instructions for a number of operating systems.

.. _details_ubuntu:

Ubuntu
======

To install the prerequisites on Ubuntu and any other Debian derived distribution, you can use the ``apt`` package manager.
The following will install the basic ``python`` requirements and the ``git`` source control manager:

.. code-block:: bash

    sudo apt-get install git python2.7-dev python-pip virtualenv

To install the requirements for the ``postgres`` database run the following:

.. code-block:: bash

    sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

For a more detailed description of database requirements and usage see the :ref:`database<database>` section.


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

To start the `postgres` database server, execute:

.. code-block:: bash

    pg_ctl -D /usr/local/var/postgres start

For a more detailed description of database requirements and usage see the :ref:`database<database>` section.

.. _details_macports:

Mac OS X (MacPorts)
===================

.. _macports: https://www.macports.org/

Another package manager for MacOS is `macports`_.

.. code-block:: bash

    sudo port install git python postgresql96 postgresql96-server

To start the ``postgres`` database server, run:

.. code-block:: bash

    sudo su postgres
    pg_ctl -D /opt/local/var/db/postgresql96/defaultdb start


.. _details_gentoo:

Gentoo Linux
============

    
.. _details_wsl:

Windows Subsystem for Linux (Ubuntu)
====================================

The guide for Ubuntu above can be followed but there are a few things to note:

#. Linux services under WSL are not started automatically.
   To start the PostgreSQL service, type the command below in the terminal::

     sudo service postgresql start

#. There is a `known issue <https://github.com/Microsoft/WSL/issues/856>`_ in WSL Ubuntu 18.04 where the timezone is not
   configured correctly out-of-the-box, which may cause problem for the database. 
   The following command can be used to re-configure the time zone::

     dpkg-reconfigure tzdata

#. The file open limit may need to be raised using ``sudo ulimit -n 2048`` (default is 1024), when running tests.


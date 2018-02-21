.. _installation_os:

Operating Systems
=================

This page provides some installation instructions for installing the prerequisite software necessary to run AiiDA.
Note that we do not officially support all platforms and cannot therefore provide instructions for all possible operating systems.


Ubuntu
------

To install the prerequisites on Ubuntu and any other Debian derived distribution, you can use the ``apt`` package manager.
The following will install the basic ``python`` requirements and the ``git`` source control manager:

.. code-block:: bash

    sudo apt-get install git python2.7-dev python-pip virtualenv

To install the requirements for the ``postgres`` database run the following:

.. code-block:: bash

    sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

For a more detailed description of database requirements and usage see the :ref:`database<database>` section.
Finally, to install the RabbitMQ message broker, run the following command:

.. code-block:: bash

    sudo apt-get install rabbitmq-server

After a reboot, RabbitMQ should be started automatically as it is added as a self starting service.
If you run into trouble, please refer to the RabbitMQ :ref:`troubleshooting section<installation_rabbitmq>`.


Mac OS X
--------

For Mac OS it is adviced to use the `Homebrew`_ package manager.
If you have not installed Homebrew yet, you can do so with the following command:

.. code-block bash::

    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

.. _Homebrew: http://brew.sh/index_de.html

After you have installed Homebrew, you can install the basic requirements as follows:

.. code-block bash::

    brew install git python postgresql

To start the `postgres` database server, execute:

.. code-block bash::

    pg_ctl -D /usr/local/var/postgres start

For a more detailed description of database requirements and usage see the :ref:`database<database>` section.
Installing the RabbitMQ message broke through Homebrew is as easy as:

.. code-block bash::

    brew install rabbitmq

To start the server and add it as a self-starting service, run:

.. code-block bash::

    brew services start rabbitmq

For more information, or if you run into trouble, please refer to the RabbitMQ :ref:`troubleshooting section<installation_rabbitmq>`.


Gentoo Linux
------------

To install RabbitMQ on a Gentoo distribution through the ``portage`` package manager run the following command:

.. code-block:: bash

    emerge -av rabbitmq-server

To make sure that RabbitMQ is started at system boot, execute:

.. code-block:: bash

    rc-update add rabbitmq

If you want to manually start the RabbitMQ server you can use:

.. code-block:: bash

    /etc/init.d/rabbitmq start

For more information, or if you run into trouble, please refer to the RabbitMQ :ref:`troubleshooting section<installation_rabbitmq>`.
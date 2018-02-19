.. _installation_rabbitmq:

RabbitMQ
========

RabbitMQ is a message queue application that allows AiiDA to send messages to the daemon.
For example when a calculation or workflow is submitted to the daemon, a launch message is send over RabbitMQ, which will be picked up by the daemon.
Therefore, for AiiDA to work properly, a RabbitMQ server needs to be installed on the machine that runs AiiDA.
In this section we will detail the installation instructions for the Ubuntu and MacOS operating systems.


Ubuntu
------

After installing RabbitMQ, potentially with a system reboot, it should be started automatically after every system boot.
You can check whether it is running by checking the status through the command:

.. code-block:: bash

    sudo rabbitmqctl status

If you are having problems installing RabbitMQ, please refer to the detailed instructions  provided on the `website of RabbitMQ itself for Debian based distributions <https://www.rabbitmq.com/install-debian.html>`_.


Mac OS X
--------

After installing RabbitMQ, potentially with a system reboot, it should be started automatically after every system boot.
You can check whether it is running by checking the status through the command:

.. code-block:: bash

    /usr/local/sbin/rabbitmqctl status

If you are having problems installing RabbitMQ, please refer to the detailed instructions provided on the `website of RabbitMQ itself for Homebrew <https://www.rabbitmq.com/install-homebrew.html>`_.
If you do not have or want to install the Homebrew package manager, but want to use ports instead, use the following commands:

.. code-block bash::

    sudo port install rabbitmq-server
    sudo launchctl load -w /Library/LaunchDaemons/org.macports.rabbitmq-server.plist


Gentoo
------

To make sure that the installation and startup was successful, you can check the status of the RabbitMQ server with:

.. code-block:: bash

    rabbitmqctl status

If you have encounter the following error

.. code-block:: bash

    Argument '-smp enable' not supported."

Remove the mentioned option from the file ``/usr/libexec/rabbitmq/rabbitmq-env`` and restart the server.
If you still have trouble getting RabbitMQ to run, please refer to the detailed instructions provided on the `website of RabbitMQ itself for generic Unix systems <https://www.rabbitmq.com/install-generic-unix.html>`_.
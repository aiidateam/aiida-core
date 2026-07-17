.. _how-to:cookbook:

========
Cookbook
========

This how-to page collects useful short scripts and code snippets that may be useful in the everyday usage of AiiDA.


Getting an ``AuthInfo`` knowing the computer and the user
=========================================================

To open a transport to a computer, you need the corresponding :class:`~aiida.orm.authinfos.AuthInfo` object, which contains the required information for a specific user.
Once you have the relevant :class:`~aiida.orm.computers.Computer` and :class:`~aiida.orm.users.User` collection, you can obtain as follows:

.. code-block:: python

    computer.get_authinfo(user)

Here is, as an example, a useful utility function:

.. code-block:: python

    def get_authinfo_from_computer_label(computer_label):
        from aiida.orm import load_computer, User
        computer = load_computer(computer_label)
        user = User.collection.get_default()
        return computer.get_authinfo(user)

that you can then use, for instance, as follows:

.. code-block:: python

    authinfo = get_authinfo_from_computer_label('localhost')
    with authinfo.get_transport() as transport:
        print(transport.listdir())

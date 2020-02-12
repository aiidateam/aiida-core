.. _working_data:

Concept
=======

The nodes in the :ref:`provenance graph<concepts_provenance>` that are the inputs and outputs of processes are referred to as `data` and are represented by :class:`~aiida.orm.nodes.data.data.Data` nodes.
Since data can come in all shapes and forms, the :class:`~aiida.orm.nodes.data.data.Data` class can be sub classed.
AiiDA ships with some basic data types such as the :class:`~aiida.orm.nodes.data.int.Int` which represents a simple integer and the :class:`~aiida.orm.nodes.data.dict.Dict`, representing a dictionary of key-value pairs.
There are also more complex data types such as the :class:`~aiida.orm.nodes.data.array.array.ArrayData` which can store multidimensional arrays of numbers.
These basic data types serve most needs for the majority of applications, but more specific solutions may be useful or even necessary.
In the next sections, we will explain :ref:`how a new data type can be created<working_data_creating_new_types>` and what :ref:`guidelines<working_data_design_guidelines>` should ideally be observed during the design process.


.. _working_data_creating_new_types:

Creating new data types
=======================

Creating a new data type is as simple as creating a new sub class of the base :class:`~aiida.orm.nodes.data.data.Data` class.

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

At this point, our new data type does nothing special.
Typically, one creates a new data type to represent a specific type of data.
For the purposes of this example, let's assume that the goal of our ``NewData`` type is to store a single numerical value.
To allow one to construct a new ``NewData`` data node with the desired ``value``, for example:

.. code:: python

    node = NewData(value=5)

we need to allow passing that value to the constructor of the node class.
Therefore, we have to override the constructor :meth:`~aiida.orm.nodes.node.Node.__init__`:

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

        def __init__(self, **kwargs)
            value = kwargs.pop('value')
            super().__init__(**kwargs)
            self.set_attribute('value', value)

.. warning::

    For the class to function properly, the signature of the constructor **cannot be changed** and the constructor of the parent class **has to be called**.

Before calling the construtor of the base class, we have to remove the ``value`` keyword from the keyword arguments ``kwargs``, because the base class will not expect it and will raise an exception if left in the keyword arguments.
The final step is to actually *store* the value that is passed by the caller of the constructor.
A new node has two locations to permanently store any of its properties:

* the database
* the file repository

The section on :ref:`design guidelines<working_data_design_guidelines>` will go into more detail what the advantages and disadvantages of each option are and when to use which.
For now, since we are storing only a single value, the easiest and best option is to use the database.
Each node has *attributes* that can store any key-value pair, as long as the value is JSON serializable.
By adding the value to the node's attributes, they will be queryable in the database once an instance of the ``NewData`` node is stored.

.. code:: python

    node = NewData(value=5)   # Creating new node instance in memory
    node.set_attribute('value', 6)  # While in memory, node attributes can be changed
    node.store()  # Storing node instance in the database

After storing the node instance in the database, its attributes are frozen, and ``node.set_attribute('value', 7)`` will fail.
By storing the ``value`` in the attributes of the node instance, we ensure that that ``value`` can be retrieved even when the node is reloaded at a later point in time.

Besides making sure that the content of a data node is stored in the database or file repository, the data type class can also provide useful methods for users to retrieve that data.
For example, with the current state of the ``NewData`` class, in order to retrieve the ``value`` of a stored ``NewData`` node, one needs to do:

.. code:: python

    node = load_node(<IDENTIFIER>)
    node.get_attribute('value')

In other words, the user of the ``NewData`` class needs to know that the ``value`` is stored as an attribute with the name 'value'.
This is not easy to remember and therefore not very user-friendly.
Since the ``NewData`` type is a class, we can give it useful methods.
Let's introduce one that will return the value that was stored for it:

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

        @property
        def value(self):
            """Return the value stored for this instance."""
            return self.get_attribute('value')

The addition of the instance property ``value`` makes retrieving the value of a ``NewData`` node a lot easier:

.. code:: python

    node = load_node(<IDENTIFIER)
    value = node.value

As said before, in addition to their attributes, data types can also store their properties in the file repository.
Imagine a data type that needs to wrap a single text file.

.. code:: python

    import os
    from aiida.orm import Data


    class TextFileData(Data):
        """Data class that can be used to wrap a single text file by storing it in its file repository."""

        def __init__(self, filepath, **kwargs):
            """Construct a new instance and set the contents to that of the file.

            :param file: an absolute filepath of the file to wrap
            """
            super().__init__(**kwargs)

            filename = os.path.basename(filepath)  # Get the filename from the absolute path
            self.put_object_from_file(filepath, filename)  # Store the file in the repository under the given filename
            self.set_attribute('filename', filename)  # Store in the attributes what the filename is

        def get_content(self):
            """Return the content of the single file stored for this data node.

            :return: the content of the file as a string
            """
            filename = self.get_attribute('filename')
            return self.get_object_content(filename)

To create a new instance of this data type and get its content:

.. code:: python

    node = TextFileData(filepath='/some/absolute/path/to/file.txt')
    node.get_content()  # This will return the content of the file

This example is a simplified version of the :class:`~aiida.orm.nodes.data.singlefile.SinglefileData` data class that ships with `aiida-core`.
If this happens to be your use case (or very close to it), it is of course better to use that class, or you can sub class it and adapt it where needed.

The two new data types we have just implemented are of course trivial and not very useful, but the concepts are flexible and can easily be applied to more complex use-cases.
The following section will provide useful guidelines on how to optimally design new data types.


.. _working_data_design_guidelines:

Database or repository?
=======================

When deciding where to store a property of a data type, one has to choose between the database and the file repository.
The database will make it possible to search in the provenance graph based on criteria based on the property, e.g. all ``NewData`` nodes where the property is greater than 0.
The downside is that storing too much information in the database can make it sluggish.
Therefore, big data (think large files), whose content does not necessarily need to be queried for, is better stored in the file repository.
Of course a data type may need to store multiple properties of varying character, but both storage locations can safely be used in parellel.
When choosing the database as the storage location, the properties should be stored using the node *attributes*.
To set and retrieve them, use the attribute methods of the :class:`~aiida.orm.nodes.node.Node` class.

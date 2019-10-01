.. _working_data:

****
Data
****

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

        attribute_name = 'value'

        def __init__(self, **kwargs)
            value = kwargs.pop(self.attribute_name)
            super(NewData, self).__init__(**kwargs)

.. warning::

    For the class to function properly, the signature of the constructor **cannot be changed** and the constructor of the parent class **has to be called**.

Before calling the construtor of the base class, we have to remove the ``value`` keyword from the keyword arguments ``kwargs``, because the base class will not expect it and will raise an exception if left in the keyword arguments.
The final step is to actually *store* the value that is passed by the caller of the constructor.
The previous snippet removes it from the ``kwargs`` but then does not do anything with it.
A new node has two locations to permanently store any of its properties:

* the database
* the file repository

The section on :ref:`design guidelines<working_data_design_guidelines>` will go into more detail what the advantages and disadvantages of each option are and when to use which.
For now, since we are storing only a single value, the easiest and best option is to use the database.
Each node has *attributes* that can store any key-value pair, as long as the value is JSON serializable.
We can use these attributes to store the ``value`` of our ``NewData`` data type:

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

        attribute_name = 'value'

        def __init__(self, **kwargs)
            value = kwargs.pop(self.attribute_name)
            super(NewData, self).__init__(**kwargs)
            self.set_attribute(self.attribute_name, value)

By adding the value to the node's attributes, after the node itself has been stored, it will be permanently recorded in the database.
Creating an instance of the ``NewData`` data type and storing it is now very easy:

.. code:: python

    node = Data(value=5)
    node.store()

By storing the ``value`` in the attributes of the node instance, we ensure that that ``value`` can be retrieved even when the node is reloaded at a later point in time.

Besides making sure that the content of a data node is stored in the database or file repository, the data type class can also provide useful methods for users to retrieve that data.
For example, with the current state of the ``NewData`` class in the last example, if a user were to load a stored ``NewData`` node and wanted to retrieve the ``value`` that it contains, they would have to do something like:

.. code:: python

    node = load_node(<IDENTIFIER>)
    node.get_attribute(NewData.attribute_name)

In other words, the user of the ``NewData`` class needs to know that the ``value`` is stored as an attribute with a name given by the class-attribute ``attribute_name``.
This is not easy to remember and therefore not very user-friendly.
Since the ``NewData`` type is a class, we can give it useful methods.
Let's introduce one that will return the value that was stored for it:

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

        attribute_name = 'value'

        @property
        def value(self):
            """Return the value stored for this instance."""
            return self.get_attribute(self.attribute_name)

The addition of the instance property ``value`` makes retrieving the value of a ``NewData`` node a lot easier:

.. code:: python

    node = load_node(<IDENTIFIER)
    value = node.value

The new data type we have just implemented is of course trivial and not very useful, but the concept is flexible and can be easily applied to more complex use-cases.
The following section will provide useful guidelines on how to optimally design new data types.


.. _working_data_design_guidelines:

Design guidelines
=================

Database or repository?
-----------------------

When deciding where to store a property of a data type, one has to choose between the database and the file repository.
The database will make the property queryable and relatively quickly accessible.
The downside is that storing too much information in the database can make it sluggish.
Therefore, big data (think large files), whose content does not necessarily need to be queried for, is better stored in the file repository.
Of course a data type may need to store multiple properties of varying character, but both storage locations can safely be used in parellel.
When choosing the database as the storage location, the properties should be stored using the node *attributes*.
To set and retrieve them, use the attribute methods of the :class:`~aiida.orm.nodes.node.Node` class.
A node's attribute is what "defines" it, which is exactly why they should be used to store these properties and why they become immutable after the node is stored.
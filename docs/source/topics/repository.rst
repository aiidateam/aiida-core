.. _topics:repository:

**********
Repository
**********

In addition to the :ref:`database <topics:database>`, AiiDA also stores information in the *repository* in the form of files.
The repository is optimized to store large amounts of files, which allows AiiDA to scale to high-throughput loads.
As a result, the files cannot be accessed directly using file system tools, despite the fact that they are stored somewhere on the local file system.
Instead, you should interact with the repository through the API.

Since each node can have its own *virtual* file hierarchy, the repository contents of a node are accessed through the :class:`~aiida.orm.nodes.node.Node` class.
The hierarchy is virtual because the files may not actually be written to disk with the same hierarchy.
For more technical information on the implementation, please refer to the :ref:`repository internals section <internal-architecture:repository>`.


.. _topics:repository:writing:

Writing to the repository
=========================

To write files to a node, you can use one of the following three methods:

* :meth:`~aiida.orm.nodes.repository.NodeRepository.put_object_from_file`
* :meth:`~aiida.orm.nodes.repository.NodeRepository.put_object_from_filelike`
* :meth:`~aiida.orm.nodes.repository.NodeRepository.put_object_from_tree`

Let's assume that you have a file on your local file system called `/some/path/file.txt` that you want to copy to a node.
The most straightforward solution is the following:

.. code:: python

    node = Node()
    node.put_object_from_file('/some/path/file.txt', 'file.txt')

Note that the first argument should be an absolute filepath.
The second argument is the filename with which the file will be written to the repository of the node.
It can be any valid filename as long as it is relative.
The target filename can contain nested subdirectories, for example `some/relative/path/file.txt`.
The nested directories do not have to exist.

Alternatively, it is also possible to write a file to a node from a stream or filelike-object.
This is useful when the content of the file is already in memory and prevents having to write it to the local filesystem first.
For example, one can do the following:

.. code:: python

    with open('/some/path/file.txt') as handle:
        node = Node()
        node.put_object_from_filelike(handle, 'file.txt')

which is the same as the previous example, except the file is opened first in a context manager and then the filelike-object is passed in.
The :meth:`~aiida.orm.nodes.repository.NodeRepository.put_object_from_filelike` method should work with any filelike-object, for example also byte- and textstreams:

.. code:: python

    import io
    node = Node()
    node.put_object_from_filelike(io.BytesIO(b'some content'), 'file.txt')

Finally, instead of writing one file at a time, you can write the contents of an entire directory to the node's repository:

.. code:: python

    node = Node()
    node.put_object_from_tree('/some/directory')

The contents of the entire directory will be recursively written to the node's repository.
Optionally, you can write the content to a subdirectory in the repository:

.. code:: python

    node = Node()
    node.put_object_from_tree('/some/directory', 'some/sub/path')

As with :meth:`~aiida.orm.nodes.repository.NodeRepository.put_object_from_file`, the sub directories do not have to be explicitly created first.


.. _topics:repository:listing:

Listing repository content
==========================

To determine the contents of a node's repository, you can use the following methods:

* :meth:`~aiida.orm.nodes.repository.NodeRepository.list_object_names`
* :meth:`~aiida.orm.nodes.repository.NodeRepository.list_objects`
* :meth:`~aiida.orm.nodes.repository.NodeRepository.walk`

The first method will return a list of file objects contained within the node's repository, where an object can be either a directory or a file:

.. code:: ipython

    In [1]: node.list_object_names()
    Out[1]: ['sub', 'file.txt']

To determine the contents of a subdirectory, simply pass the path as an argument:

.. code:: ipython

    In [1]: node.list_object_names('sub/directory')
    Out[1]: ['nested.txt']

Note that the elements in the returned list are simple strings and so one cannot tell if they correspond to a directory or a file.
If this information is needed, use :meth:`~aiida.orm.nodes.repository.NodeRepository.list_objects` instead.
This method returns a list of :class:`~aiida.repository.common.File` objects.
These objects have a :meth:`~aiida.repository.common.File.file_type` and :meth:`~aiida.repository.common.File.name` property which returns the type and name of the file object, respectively.
An example usage would be the following:

.. code:: python

    from aiida.repository.common import FileType

    for obj in node.list_objects():
        if obj.file_type == FileType.DIRECTORY:
            print(f'{obj.name} is a directory.)
        elif obj.file_type == FileType.FILE:
            print(f'{obj.name} is a file.)

To retrieve a specific file object with a particular relative path, use :meth:`~aiida.orm.nodes.repository.NodeRepository.get_object`:

.. code:: ipython

    In [1]: node.get_object('sub/directory/nested.txt')
    Out[1]: File(file_type=FileType.FILE, name='nested.txt')

Finally, if you want to recursively iterate over the contents of a node's repository, you can use the :meth:`~aiida.orm.nodes.repository.NodeRepository.walk` method.
It operates exactly as the |os.walk|_:

.. code:: ipython

    In [1]: for root, dirnames, filenames in node.walk():
                print(root, dirnames, filenames)
    Out[1]: '.', ['sub'], ['file.txt']
            'sub', ['directory'], []
            'sub/directory', [], ['nested.txt']


.. _topics:repository:reading:

Reading from the repository
===========================

To retrieve the content of files stored in a node's repository, you can use the following methods:

* :meth:`~aiida.orm.nodes.repository.NodeRepository.open`
* :meth:`~aiida.orm.nodes.repository.NodeRepository.get_object_content`

The first method functions exactly as Python's ``open`` built-in function:

.. code:: python

    with node.open('some/file.txt', 'r') as handle:
        content = handle.read()

The :meth:`~aiida.orm.nodes.repository.NodeRepository.get_object_content` method provides a short-cut for this operation in case you want to directly read the content into memory:

.. code:: python

    content node.get_object_content('some/file.txt', 'r')

Both methods accept a second argument to determine whether the file should be opened in text- or binary-mode.
The valid values are ``'r'`` and ``'rb'``, respectively.
Note that these methods can only be used to read content from the repository and so any other read modes, such as ``'wb'``, will result in an exception.
To write files to the repository, use the methods that are described in the section on :ref:`writing to the repository <topics:repository:writing>`.


.. _topics:repository:copying:

Copying from the repository
===========================

If you want to copy specific files from a node's repository, the section on :ref:`reading from the repository<topics:repository:reading>` shows how to read their content which can then be written elsewhere.
However, sometimes you want to copy the entire contents of the node's repository, or a subdirectory of it.
The :meth:`~aiida.orm.nodes.repository.NodeRepository.copy_tree` method makes this easy and can be used as follows:

.. code:: python

    node.copy_tree('/some/target/directory')

which will write the entire repository content of ``node`` to the directory ``/some/target/directory`` on the local file system.
If you only want to copy a particular subdirectory of the repository, you can pass this as the second ``path`` argument:

.. code:: python

    node.copy_tree('/some/target/directory', path='sub/directory')

This method, combined with :meth:`~aiida.orm.nodes.repository.NodeRepository.put_object_from_tree`, makes it easy to copy the entire repository content (or a subdirectory) from one node to another:

.. code:: python

    import tempfile
    node_source = load_node(<PK>)
    node_target = Node()

    with tempfile.TemporaryDirectory() as dirpath:
        node_source.copy_tree(dirpath)
        node_target.put_object_from_tree(dirpath)

Note that this method is not the most efficient as the files are first written from ``node_a`` to a temporary directory on disk, before they are read in memory again and written to the repository of ``node_b``.
There is a more efficient method which requires a bit more code and that directly uses the :meth:`~aiida.orm.nodes.repository.NodeRepository.walk` method explained in the section on :ref:`listing repository content <topics:repository:listing>`.

.. code:: python

    node_source = load_node(<PK>)
    node_target = Node()

    for root, dirnames, filenames in node_source.walk():
        for filename in filenames:
            filepath = root / filename
            with node_source.open(filepath) as handle:
                node_target.put_object_from_filelike(handle, filepath)

.. note:: In the example above, only the files are explicitly copied over.
    Any intermediate nested directories will be automatically created in the virtual hierarchy.
    However, currently it is not possible to create a directory explicitly.
    Empty directories are not yet supported.


.. |os.walk| replace:: ``os.walk`` method of the Python standard library
.. _os.walk: https://docs.python.org/3/library/os.html#os.walk

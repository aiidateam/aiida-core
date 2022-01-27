.. _reference:api:public:

Overview of public API
----------------------

The top-level package of the ``aiida-core`` distribution is called ``aiida``.
It contains various sub-packages that we refer to as "second-level packages".

.. admonition:: Rule
    :class: tip title-icon-lightbulb

    **Any resource that can be imported directly from the top level or from a second-level package is part of the public python API** and intended for external use.
    Resources at deeper nesting level are considered internal and are not intended for use outside ``aiida-core``.

    For example:

    .. code-block:: python

        from aiida import load_profile  # OK, top-level import
        from aiida.orm import QueryBuilder  # OK, second-level import
        from aiida.tools.importexport import Archive # NOT PUBLIC API

.. warning::

    The interface and implementation of resources that are *not* considered part of the public API can change between minor AiiDA releases, and can even be moved or fully removed, without a deprecation period whatsoever.
    Be aware that scripts or AiiDA plugins that rely on such resources, can therefore break unexpectedly in between minor AiiDA releases.

Below we provide a list of the resources per second-level package that are exposed in this way.
If a module is mentioned, then all the resources defined in its ``__all__`` are included


``aiida.cmdline``
.................

::

    params.arguments
    params.options
    params.types
    utils.decorators
    utils.echo


``aiida.common``
................

::

    datastructures
    exceptions
    extendeddicts
    links
    log


``aiida.engine``
................

::

    Process
    ProcessState
    ToContext
    assign_
    append_
    WorkChain
    while_
    return_
    if_
    CalcJob
    calcfunction
    workfunction
    ExitCode
    run
    run_get_node
    run_get_pid
    submit


``aiida.orm``
.............

::

    Node
    Data
    ProcessNode
    CalcFunctionNode
    CalcJobNode
    WorkFunctionNode
    WorkChainNode
    ArrayData
    BandsData
    KpointsData
    ProjectionData
    TrajectoryData
    XyData
    Bool
    Float
    Int
    Str
    List
    ParameterData
    CifData
    Code
    FolderData
    OrbitalData
    RemoteData
    SinglefileData
    StructureData
    UpfData
    Comment
    Computer
    Group
    Log
    QueryBuilder
    User
    load_node
    load_code
    load_computer
    load_group


``aiida.parsers``
.................

::

    Parser


``aiida.plugins``
.................

::

    entry_point
    CalculationFactory
    DataFactory
    DbImporterFactory
    ParserFactory
    SchedulerFactory
    TransportFactory
    WorkflowFactory


``aiida.scheduler``
...................

::

    Scheduler


``aiida.tools``
...............

::

    CalculationTools
    get_kpoints_path
    get_explicit_kpoints_path
    structure_to_spglib_tuple
    spglib_tuple_to_structure
    DbImporter


``aiida.transport``
...................

::

    Transport

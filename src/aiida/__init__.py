###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA is a flexible and scalable informatics' infrastructure to manage,
preserve, and disseminate the simulations, data, and workflows of
modern-day computational science.

Able to store the full provenance of each object, and based on a
tailored database built for efficient data mining of heterogeneous results,
AiiDA gives the user the ability to interact seamlessly with any number of
remote HPC resources and codes, thanks to its flexible plugin interface
and workflow engine for the automation of complex sequences of simulations.

More information at http://www.aiida.net
"""

from aiida.brokers import *
from aiida.calculations import *
from aiida.cmdline import *
from aiida.common import *
from aiida.common.log import configure_logging
from aiida.engine import *
from aiida.manage import *
from aiida.manage.configuration import get_config_option, get_profile, load_profile, profile_context
from aiida.orm import *
from aiida.parsers import *
from aiida.plugins import *
from aiida.repository import *
from aiida.schedulers import *
from aiida.storage import *
from aiida.tools import *
from aiida.transports import *

__copyright__ = (
    'Copyright (c), This file is part of the AiiDA platform. '
    'For further information please visit http://www.aiida.net/. All rights reserved.'
)
__license__ = 'MIT license, see LICENSE.txt file.'
__version__ = '2.6.2.post0'
__authors__ = 'The AiiDA team.'
__paper__ = (
    'S. P. Huber et al., "AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and '
    'data provenance", Scientific Data 7, 300 (2020); https://doi.org/10.1038/s41597-020-00638-4'
)
__paper_short__ = 'S. P. Huber et al., Scientific Data 7, 300 (2020).'

__all__ = [  # noqa: RUF022
    'configure_logging',
    'get_config_option',
    'get_file_header',
    'get_profile',
    'get_strict_version',
    'get_version',
    'load_ipython_extension',
    'load_profile',
    'profile_context',
    # aiida.orm
    'ASCENDING',
    'DESCENDING',
    'AbstractCode',
    'AbstractNodeMeta',
    'ArrayData',
    'AttributeManager',
    'AuthInfo',
    'AutoGroup',
    'BandsData',
    'BaseType',
    'Bool',
    'CalcFunctionNode',
    'CalcJobNode',
    'CalcJobResultManager',
    'CalculationEntityLoader',
    'CalculationNode',
    'CifData',
    'Code',
    'CodeEntityLoader',
    'Collection',
    'Comment',
    'Computer',
    'ComputerEntityLoader',
    'ContainerizedCode',
    'Data',
    'Dict',
    'Entity',
    'EntityExtras',
    'EntityTypes',
    'EnumData',
    'Float',
    'FolderData',
    'Group',
    'GroupEntityLoader',
    'ImportGroup',
    'InstalledCode',
    'Int',
    'JsonableData',
    'Kind',
    'KpointsData',
    'LinkManager',
    'LinkPair',
    'LinkTriple',
    'List',
    'Log',
    'Node',
    'NodeAttributes',
    'NodeEntityLoader',
    'NodeLinksManager',
    'NodeRepository',
    'NumericType',
    'OrbitalData',
    'OrderSpecifier',
    'OrmEntityLoader',
    'PortableCode',
    'ProcessNode',
    'ProjectionData',
    'QbField',
    'QbFieldFilters',
    'QbFields',
    'QueryBuilder',
    'RemoteData',
    'RemoteStashData',
    'RemoteStashFolderData',
    'SinglefileData',
    'Site',
    'Str',
    'StructureData',
    'TrajectoryData',
    'UpfData',
    'UpfFamily',
    'User',
    'WorkChainNode',
    'WorkFunctionNode',
    'WorkflowNode',
    'XyData',
    'cif_from_ase',
    'find_bandgap',
    'get_loader',
    'get_query_type_from_type_string',
    'get_type_string_from_class',
    'has_pycifrw',
    'load_code',
    'load_computer',
    'load_entity',
    'load_group',
    'load_node',
    'load_node_class',
    'pycifrw_from_cif',
    'to_aiida_type',
    'validate_link',
    # aiida.engine
    'PORT_NAMESPACE_SEPARATOR',
    'AiiDAPersister',
    'Awaitable',
    'AwaitableAction',
    'AwaitableTarget',
    'BaseRestartWorkChain',
    'CalcJob',
    'CalcJobImporter',
    'CalcJobOutputPort',
    'CalcJobProcessSpec',
    'DaemonClient',
    'ExitCode',
    'ExitCodesNamespace',
    'FunctionProcess',
    'InputPort',
    'InterruptableFuture',
    'JobManager',
    'JobsList',
    'ObjectLoader',
    'OutputPort',
    'PastException',
    'PortNamespace',
    'Process',
    'ProcessBuilder',
    'ProcessBuilderNamespace',
    'ProcessFuture',
    'ProcessHandlerReport',
    'ProcessSpec',
    'ProcessState',
    'Runner',
    'ToContext',
    'WithNonDb',
    'WithSerialize',
    'WorkChain',
    'append_',
    'assign_',
    'await_processes',
    'calcfunction',
    'construct_awaitable',
    'get_daemon_client',
    'get_object_loader',
    'if_',
    'interruptable_task',
    'is_process_function',
    'process_handler',
    'return_',
    'run',
    'run_get_node',
    'run_get_pk',
    'submit',
    'while_',
    'workfunction',
    # aiida.calculations
    'CalculationTools',
    # aiida.cmdline
    'AbsolutePathParamType',
    'CalculationParamType',
    'CodeParamType',
    'ComputerParamType',
    'ConfigOptionParamType',
    'DataParamType',
    'DynamicEntryPointCommandGroup',
    'EmailType',
    'EntryPointType',
    'FileOrUrl',
    'GroupParamType',
    'HostnameType',
    'IdentifierParamType',
    'LabelStringType',
    'LazyChoice',
    'MpirunCommandParamType',
    'MultipleValueParamType',
    'NodeParamType',
    'NonEmptyStringParamType',
    'PathOrUrl',
    'PluginParamType',
    'ProcessParamType',
    'ProfileParamType',
    'ShebangParamType',
    'UserParamType',
    'VerdiCommandGroup',
    'WorkflowParamType',
    'dbenv',
    'echo_critical',
    'echo_dictionary',
    'echo_error',
    'echo_info',
    'echo_report',
    'echo_success',
    'echo_tabulate',
    'echo_warning',
    'format_call_graph',
    'is_verbose',
    'only_if_daemon_running',
    'with_dbenv',
    # aiida.common
    'AIIDA_LOGGER',
    'TQDM_BAR_FORMAT',
    'AiidaException',
    'AttributeDict',
    'CalcInfo',
    'CalcJobState',
    'ClosedStorage',
    'CodeInfo',
    'CodeRunMode',
    'ConfigurationError',
    'ConfigurationVersionError',
    'ContentNotExistent',
    'CorruptStorage',
    'DbContentError',
    'DefaultFieldsAttributeDict',
    'EntryPointError',
    'FailedError',
    'FeatureDisabled',
    'FeatureNotAvailable',
    'FixedFieldsAttributeDict',
    'GraphTraversalRule',
    'GraphTraversalRules',
    'HashingError',
    'IncompatibleStorageSchema',
    'InputValidationError',
    'IntegrityError',
    'InternalError',
    'InvalidEntryPointTypeError',
    'InvalidOperation',
    'LicensingException',
    'LinkType',
    'LoadingEntryPointError',
    'LockedProfileError',
    'LockingProfileError',
    'MissingConfigurationError',
    'MissingEntryPointError',
    'ModificationNotAllowed',
    'MultipleEntryPointError',
    'MultipleObjectsError',
    'NotExistent',
    'NotExistentAttributeError',
    'NotExistentKeyError',
    'OutputParsingError',
    'ParsingError',
    'PluginInternalError',
    'ProfileConfigurationError',
    'ProgressReporterAbstract',
    'RemoteOperationError',
    'StashMode',
    'StorageMigrationError',
    'StoringNotAllowed',
    'TestsNotAllowedError',
    'TransportTaskException',
    'UniquenessError',
    'UnsupportedSpeciesError',
    'ValidationError',
    'create_callback',
    'get_progress_reporter',
    'override_log_level',
    'set_progress_bar_tqdm',
    'set_progress_reporter',
    'validate_link_label',
    # aiida.manage
    'CURRENT_CONFIG_VERSION',
    'MIGRATIONS',
    'OLDEST_COMPATIBLE_CONFIG_VERSION',
    'Option',
    'Profile',
    'check_and_migrate_config',
    'config_needs_migrating',
    'disable_caching',
    'downgrade_config',
    'enable_caching',
    'get_current_version',
    'get_manager',
    'get_option',
    'get_option_names',
    'get_use_cache',
    'parse_option',
    'upgrade_config',
    # aiida.parsers
    'Parser',
    # aiida.plugins
    'BaseFactory',
    'CalcJobImporterFactory',
    'CalculationFactory',
    'DataFactory',
    'DbImporterFactory',
    'GroupFactory',
    'OrbitalFactory',
    'ParserFactory',
    'PluginVersionProvider',
    'SchedulerFactory',
    'StorageFactory',
    'TransportFactory',
    'WorkflowFactory',
    'get_entry_points',
    'load_entry_point',
    'load_entry_point_from_string',
    'parse_entry_point',
    # aiida.repository
    'AbstractRepositoryBackend',
    'DiskObjectStoreRepositoryBackend',
    'File',
    'FileType',
    'Repository',
    'SandboxRepositoryBackend',
    # aiida.schedulers
    'BashCliScheduler',
    'JobInfo',
    'JobResource',
    'JobState',
    'JobTemplate',
    'MachineInfo',
    'NodeNumberJobResource',
    'ParEnvJobResource',
    'Scheduler',
    'SchedulerError',
    'SchedulerParsingError',
    # aiida.storage
    'SqliteDosStorage',
    # aiida.tools
    'DELETE_LOGGER',
    'CalculationTools',
    'Graph',
    'GroupNotFoundError',
    'GroupNotUniqueError',
    'GroupPath',
    'InvalidPath',
    'NoGroupsInPathError',
    'Orbital',
    'RealhydrogenOrbital',
    'default_link_styles',
    'default_node_styles',
    'default_node_sublabels',
    'delete_group_nodes',
    'delete_nodes',
    'get_explicit_kpoints_path',
    'get_kpoints_path',
    'pstate_node_styles',
    'spglib_tuple_to_structure',
    'structure_to_spglib_tuple',
    # aiida.transports
    'SshTransport',
    'Transport',
    'convert_to_bool',
    'parse_sshconfig',
]


def get_strict_version():
    """Return a distutils StrictVersion instance with the current distribution version

    :returns: StrictVersion instance with the current version
    :rtype: :class:`!distutils.version.StrictVersion`
    """
    import sys

    if sys.version_info >= (3, 12):
        msg = 'Cannot use get_strict_version() with Python 3.12 and newer'
        raise RuntimeError(msg)
    else:
        from distutils.version import StrictVersion

        from aiida.common.warnings import warn_deprecation

        warn_deprecation(
            'This method is deprecated as the `distutils` package it uses will be removed in Python 3.12.', version=3
        )
        return StrictVersion(__version__)


def get_version() -> str:
    """Return the current AiiDA distribution version

    :returns: the current version
    """
    return __version__


def _get_raw_file_header() -> str:
    """Get the default header for source AiiDA source code files.
    Note: is not preceded by comment character.

    :return: default AiiDA source file header
    """
    return f"""This file has been created with AiiDA v. {__version__}
If you use AiiDA for publication purposes, please cite:
{__paper__}
"""


def get_file_header(comment_char: str = '# ') -> str:
    """Get the default header for source AiiDA source code files.

    .. note::

        Prepend by comment character.

    :param comment_char: string put in front of each line

    :return: default AiiDA source file header
    """
    lines = _get_raw_file_header().splitlines()
    return '\n'.join(f'{comment_char}{line}' for line in lines)


def load_ipython_extension(ipython):
    """Load the AiiDA IPython extension, using ``%load_ext aiida``.

    :param ipython: InteractiveShell instance. If ``None``, the global InteractiveShell is used.
    """
    from aiida.tools.ipython.ipython_magics import load_ipython_extension

    load_ipython_extension(ipython)

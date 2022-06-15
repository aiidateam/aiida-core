# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Defines aliases for AiiDA ORM classes in sphinx autodoc.

This allows documentation authors to continue to use `:py:class:`aiida.orm.Dict` instead of
instead of `:py:class:`aiida.orm.nodes.data.dict.Dict`, until a better solution is found.
See 8a5d8017e8cd09d7e477aa41c8a07bb24a35e58 for details.
"""

from sphinx.addnodes import pending_xref
from sphinx.transforms import SphinxTransform

# these are mainly required, because sphinx finds multiple references,
# in `aiida.orm`` and `aiida.restapi.translator`
autodoc_aliases_typing = {
    'Code': 'aiida.orm.nodes.data.code.legacy.Code',
    'Computer': 'aiida.orm.computers.Computer',
    'Data': 'aiida.orm.nodes.data.data.Data',
    'Group': 'aiida.orm.groups.Group',
    'Node': 'aiida.orm.nodes.node.Node',
    'User': 'aiida.orm.users.User',
    'ExitCode': 'aiida.engine.processes.exit_code.ExitCode',
    'QueryBuilder': 'aiida.orm.querybuilder.QueryBuilder',
    'WorkChainNode': 'aiida.orm.nodes.process.workflow.workchain.WorkChainNode',
    'orm.ProcessNode': 'aiida.orm.nodes.process.process.ProcessNode',
    'BackendAuthInfo': 'aiida.orm.implementation.authinfos.BackendAuthInfo',
    'BackendComment': 'aiida.orm.implementation.comments.BackendComment',
    'BackendComputer': 'aiida.orm.implementation.computers.BackendComputer',
    'BackendGroup': 'aiida.orm.implementation.groups.BackendGroup',
    'BackendLog': 'aiida.orm.implementation.logs.BackendLog',
    'BackendNode': 'aiida.orm.implementation.nodes.BackendNode',
    'BackendUser': 'aiida.orm.implementation.users.BackendUser',
}
# alias public APIs, exposed by __all__
autodoc_aliases_public = {
    'aiida.common.CalcInfo': 'aiida.common.datastructures.CalcInfo',
    'aiida.common.CodeInfo': 'aiida.common.datastructures.CodeInfo',
    'aiida.engine.ProcessHandlerReport': 'aiida.engine.processes.workchains.utils.ProcessHandlerReport',
    'aiida.engine.run': 'aiida.engine.launch.run',
    'aiida.engine.submit': 'aiida.engine.launch.submit',
    'aiida.engine.process_handler': 'aiida.engine.processes.workchains.utils.process_handler',
    'aiida.engine.BaseRestartWorkChain': 'aiida.engine.processes.workchains.restart.BaseRestartWorkChain',
    'aiida.engine.CalcJob': 'aiida.engine.processes.calcjobs.calcjob.CalcJob',
    'aiida.engine.Process': 'aiida.engine.processes.process.Process',
    'aiida.engine.WorkChain': 'aiida.engine.processes.workchains.workchain.WorkChain',
    'aiida.engine.WorkChainSpec': 'aiida.engine.processes.workchains.workchain.WorkChainSpec',
    'aiida.orm.QueryBuilder': 'aiida.orm.querybuilder.QueryBuilder',
    'aiida.orm.ArrayData': 'aiida.orm.nodes.data.array.array.ArrayData',
    'aiida.orm.AuthInfo': 'aiida.orm.authinfos.AuthInfo',
    'aiida.orm.Computer': 'aiida.orm.computers.Computer',
    'aiida.orm.Comment': 'aiida.orm.comments.Comment',
    'aiida.orm.EnumData': 'aiida.orm.nodes.data.enum.EnumData',
    'aiida.orm.Group': 'aiida.orm.groups.Group',
    'aiida.orm.JsonableData': 'aiida.orm.nodes.data.jsonable.JsonableData',
    'aiida.orm.List': 'aiida.orm.nodes.data.list.List',
    'aiida.orm.Log': 'aiida.orm.logs.Log',
    'aiida.orm.Node': 'aiida.orm.nodes.node.Node',
    'aiida.orm.User': 'aiida.orm.users.User',
    'aiida.orm.CalculationNode': 'aiida.orm.nodes.process.calculation.calculation.CalculationNode',
    'aiida.orm.CalcJobNode': 'aiida.orm.nodes.process.calculation.calcjob.CalcJobNode',
    'aiida.orm.Code': 'aiida.orm.nodes.data.code.legacy.Code',
    'aiida.orm.Data': 'aiida.orm.nodes.data.data.Data',
    'aiida.orm.Dict': 'aiida.orm.nodes.data.dict.Dict',
    'aiida.orm.ProcessNode': 'aiida.orm.nodes.process.process.ProcessNode',
    'aiida.orm.RemoteData': 'aiida.orm.nodes.data.remote.base.RemoteData',
    'aiida.orm.WorkChainNode': 'aiida.orm.nodes.process.workflow.workchain.WorkChainNode',
    'aiida.orm.XyData': 'aiida.orm.nodes.data.array.xy.XyData',
    'aiida.orm.load_computer': 'aiida.orm.utils.loaders.load_computer',
}
autodoc_aliases_exc = {}
for exc_name in (
    'AiidaException', 'NotExistent', 'NotExistentAttributeError', 'NotExistentKeyError', 'MultipleObjectsError',
    'RemoteOperationError', 'ContentNotExistent', 'FailedError', 'StoringNotAllowed', 'ModificationNotAllowed',
    'IntegrityError', 'UniquenessError', 'EntryPointError', 'MissingEntryPointError', 'MultipleEntryPointError',
    'LoadingEntryPointError', 'InvalidEntryPointTypeError', 'InvalidOperation', 'ParsingError', 'InternalError',
    'PluginInternalError', 'ValidationError', 'ConfigurationError', 'ProfileConfigurationError',
    'MissingConfigurationError', 'ConfigurationVersionError', 'IncompatibleStorageSchema', 'CorruptStorage',
    'DbContentError', 'InputValidationError', 'FeatureNotAvailable', 'FeatureDisabled', 'LicensingException',
    'TestsNotAllowedError', 'UnsupportedSpeciesError', 'TransportTaskException', 'OutputParsingError', 'HashingError',
    'StorageMigrationError', 'LockedProfileError', 'LockingProfileError', 'ClosedStorage'
):
    autodoc_aliases_exc[f'aiida.common.{exc_name}'] = f'aiida.common.exceptions.{exc_name}'


class AutodocAliases(SphinxTransform):
    """Replace autodoc aliases.

    This converts references to objects in top-level modules to the actual object module,
    for example, ``aiida.orm.Group`` to ``aiida.orm.groups.Group``.
    """

    default_priority = 999

    def apply(self, **kwargs) -> None:
        for node in self.document.traverse(pending_xref):
            if node.get('refdomain') != 'py':
                continue
            if node.get('reftype') == 'exc' and node.get('reftarget') in autodoc_aliases_exc:
                node['reftarget'] = autodoc_aliases_exc[node.get('reftarget')]
            elif node.get('reftarget').startswith('t.'):
                node['reftarget'] = 'typing.' + node.get('reftarget')[2:]
            elif node.get('reftarget') in autodoc_aliases_typing:
                node['reftarget'] = autodoc_aliases_typing[node.get('reftarget')]
            elif node.get('reftarget') in autodoc_aliases_public:
                node['reftarget'] = autodoc_aliases_public[node.get('reftarget')]
            elif node.get('reftarget').startswith('aiida.'):
                for original, new in autodoc_aliases_public.items():
                    if node.get('reftarget').startswith(original + '.'):
                        node['reftarget'] = node.get('reftarget').replace(original, new)
                        break

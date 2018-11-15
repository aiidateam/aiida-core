# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function

from __future__ import absolute_import
import fastentrypoints
import re
import sys
from distutils.version import StrictVersion
from os import path
from setuptools import setup, find_packages
from setup_requirements import install_requires, extras_require

if __name__ == '__main__':
    # Get the version number
    aiida_folder = path.split(path.abspath(__file__))[0]
    fname = path.join(aiida_folder, 'aiida', '__init__.py')
    with open(fname) as aiida_init:
        match_expr = "__version__[^'\"]+(['\"])([^'\"]+)"
        aiida_version = re.search(match_expr, aiida_init.read()).group(2).strip()

    # Ensure that pip is installed and the version is at least 10.0.0, which is required for the build process
    try:
        import pip
    except ImportError:
        print('Could not import pip, which is required for installation')
        sys.exit(1)

    PIP_REQUIRED_VERSION = '10.0.0'
    required_version = StrictVersion(PIP_REQUIRED_VERSION)
    installed_version = StrictVersion(pip.__version__)

    if installed_version < required_version:
        print('The installation requires pip>={}, whereas currently {} is installed'.format(required_version, installed_version))
        sys.exit(1)

    bin_folder = path.join(aiida_folder, 'bin')
    setup(
        name='aiida-core',
        url='http://www.aiida.net/',
        license='MIT License',
        author="The AiiDA team",
        author_email='developers@aiida.net',
        include_package_data=True, # puts non-code files into the distribution, reads list from MANIFEST.in
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Operating System :: POSIX :: Linux',
            'Operating System :: MacOS :: MacOS X',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Topic :: Scientific/Engineering',
        ],
        version=aiida_version,
        install_requires=install_requires,
        extras_require=extras_require,
        packages=find_packages(),
        reentry_register=True,
        reentry_scan=['aiida'],
        entry_points={
            'console_scripts': [
                'verdi=aiida.cmdline.commands.cmd_verdi:verdi',
            ],
            # following are AiiDA plugin entry points:
            'aiida.calculations': [
                'arithmetic.add = aiida.calculations.plugins.arithmetic.add:ArithmeticAddCalculation',
                'templatereplacer = aiida.calculations.plugins.templatereplacer:TemplatereplacerCalculation',
            ],
            'aiida.cmdline.computer.configure': [
                'ssh = aiida.transport.plugins.ssh:CONFIGURE_SSH_CMD',
                'local = aiida.transport.plugins.local:CONFIGURE_LOCAL_CMD',
            ],
            'aiida.data': [
                'base = aiida.orm.data:BaseType',
                'numeric = aiida.orm.data.numeric:NumericType',
                'bool = aiida.orm.data.bool:Bool',
                'float = aiida.orm.data.float:Float',
                'int = aiida.orm.data.int:Int',
                'code = aiida.orm.data.code:Code',
                'list = aiida.orm.data.list:List',
                'str = aiida.orm.data.str:Str',
                'frozendict = aiida.orm.data.frozendict:FrozenDict',
                'array = aiida.orm.data.array:ArrayData',
                'array.bands = aiida.orm.data.array.bands:BandsData',
                'array.kpoints = aiida.orm.data.array.kpoints:KpointsData',
                'array.projection = aiida.orm.data.array.projection:ProjectionData',
                'array.trajectory = aiida.orm.data.array.trajectory:TrajectoryData',
                'array.xy = aiida.orm.data.array.xy:XyData',
                'cif = aiida.orm.data.cif:CifData',
                'error = aiida.orm.data.error:Error',
                'folder = aiida.orm.data.folder:FolderData',
                'parameter = aiida.orm.data.parameter:ParameterData',
                'remote = aiida.orm.data.remote:RemoteData',
                'singlefile = aiida.orm.data.singlefile:SinglefileData',
                'structure = aiida.orm.data.structure:StructureData',
                'upf = aiida.orm.data.upf:UpfData',
                'orbital = aiida.orm.data.orbital:OrbitalData',
            ],
            'aiida.node': [
                'node = aiida.orm.node:Node',
                'process = aiida.orm.node.process.process:ProcessNode',
                'process.calculation = aiida.orm.node.process.calculation.calculation:CalculationNode',
                'process.workflow = aiida.orm.node.process.workflow.workflow:WorkflowNode',
                'process.calculation.calcfunction = aiida.orm.node.process.calculation.calcfunction:CalcFunctionNode',
                'process.calculation.calcjob = aiida.orm.node.process.calculation.calcjob:CalcJobNode',
                'process.workflow.workchain = aiida.orm.node.process.workflow.workchain:WorkChainNode',
                'process.workflow.workfunction = aiida.orm.node.process.workflow.workfunction:WorkFunctionNode',
            ],
            'aiida.cmdline': [],
            'aiida.parsers': [
                'arithmetic.add = aiida.parsers.plugins.arithmetic.add:ArithmeticAddParser',
                'templatereplacer.doubler = aiida.parsers.plugins.templatereplacer.doubler:TemplatereplacerDoublerParser',
            ],
            'aiida.schedulers': [
                'direct = aiida.scheduler.plugins.direct:DirectScheduler',
                'lsf = aiida.scheduler.plugins.lsf:LsfScheduler',
                'sge = aiida.scheduler.plugins.sge:SgeScheduler',
                'slurm = aiida.scheduler.plugins.slurm:SlurmScheduler',
                'pbspro = aiida.scheduler.plugins.pbspro:PbsproScheduler',
                'torque = aiida.scheduler.plugins.torque:TorqueScheduler',
            ],
            'aiida.transports': [
                'ssh = aiida.transport.plugins.ssh:SshTransport',
                'local = aiida.transport.plugins.local:LocalTransport',
            ],
            'aiida.workflows': [
            ],
            'aiida.tools.dbexporters': [
                'tcod = aiida.tools.dbexporters.tcod'
            ],
            'aiida.tests': [],
            'aiida.tools.dbimporters': [
                'cod = aiida.tools.dbimporters.plugins.cod:CodDbImporter',
                'icsd = aiida.tools.dbimporters.plugins.icsd:IcsdDbImporter',
                'mpod = aiida.tools.dbimporters.plugins.mpod:MpodDbImporter',
                'mpds = aiida.tools.dbimporters.plugins.mpds:MpdsDbImporter',
                'materialsproject = aiida.tools.dbimporters.plugins.materialsproject:MaterialsProjectImporter',
                'nninc = aiida.tools.dbimporters.plugins.nninc:NnincDbImporter',
                'oqmd = aiida.tools.dbimporters.plugins.oqmd:OqmdDbImporter',
                'pcod = aiida.tools.dbimporters.plugins.pcod:PcodDbImporter',
                'tcod = aiida.tools.dbimporters.plugins.tcod:TcodDbImporter'
            ]
        },
        scripts=['bin/runaiida'],
        long_description=open(path.join(aiida_folder, 'README.md')).read(),
    )

# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import fastentrypoints
import re
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
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
        ],
        version=aiida_version,
        install_requires=install_requires,
        extras_require=extras_require,
        packages=find_packages(),
        # Don't forget to install it as well (by adding to the install_requires)
        setup_requires=[
            'reentry >= 1.0.3',
        ],
        reentry_register=True,
        entry_points={
            'console_scripts': [
                'verdi=aiida.cmdline.verdilib:run',
                'verdi-plug = aiida.cmdline.verdi_plug:verdi_plug'
            ],
            # following are AiiDA plugin entry points:
            'aiida.calculations': [
                'calculation = aiida.orm.calculation:Calculation',
                'function = aiida.orm.calculation.function:FunctionCalculation',
                'inline = aiida.orm.calculation.inline:InlineCalculation',
                'job = aiida.orm.calculation.job:JobCalculation',
                'work = aiida.orm.calculation.work:WorkCalculation',
                'simpleplugins.templatereplacer = aiida.orm.calculation.job.simpleplugins.templatereplacer:TemplatereplacerCalculation',
            ],
            'aiida.code': [
                'code = aiida.orm.code:Code'
            ],
            'aiida.data': [
                'bool = aiida.orm.data.bool:Bool',
                'float = aiida.orm.data.float:Float',
                'int = aiida.orm.data.int:Int',
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
                'node = aiida.orm.node:Node'
            ],
            'aiida.cmdline': [],
            'aiida.parsers': [
                'simpleplugins.templatereplacer.doubler = aiida.parsers.simpleplugins.templatereplacer.doubler:TemplatereplacerDoublerParser',
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
                'nninc = aiida.tools.dbimporters.plugins.nninc:NnincDbImporter',
                'oqmd = aiida.tools.dbimporters.plugins.oqmd:OqmdDbImporter',
                'pcod = aiida.tools.dbimporters.plugins.pcod:PcodDbImporter',
                'tcod = aiida.tools.dbimporters.plugins.tcod:TcodDbImporter'
            ]
        },
        scripts=['bin/runaiida'],
        long_description=open(path.join(aiida_folder, 'README.rst')).read(),
    )

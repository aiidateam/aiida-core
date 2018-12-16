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
        print 'Could not import pip, which is required for installation'
        sys.exit(1)

    PIP_REQUIRED_VERSION = '10.0.0'
    required_version = StrictVersion(PIP_REQUIRED_VERSION)
    installed_version = StrictVersion(pip.__version__)

    if installed_version < required_version:
        print 'The installation requires pip>={}, whereas currently {} is installed'.format(required_version, installed_version)
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
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
        ],
        version=aiida_version,
        install_requires=install_requires,
        extras_require=extras_require,
        packages=find_packages(),
        # Don't forget to install it as well (by adding to the install_requires
        reentry_register=True,
        entry_points={
            'console_scripts': [
                'verdi=aiida.cmdline.verdilib:run',
            ],
            # following are AiiDA plugin entry points:
            'aiida.calculations': [
                'simpleplugins.templatereplacer = aiida.orm.calculation.job.simpleplugins.templatereplacer:TemplatereplacerCalculation',
            ],
            'aiida.data':[
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
                'upf = aiida.orm.data.upf:UpfData'
            ],
            'aiida.cmdline': [],
            'aiida.parsers': [
                'simpleplugins.templatereplacer.test.doubler = aiida.parsers.simpleplugins.templatereplacer.test:TemplatereplacerDoublerParser',
            ],
            'aiida.schedulers': [
                'direct = aiida.scheduler.plugins.direct:DirectScheduler',
                'slurm = aiida.scheduler.plugins.slurm:SlurmScheduler',
                'pbspro = aiida.scheduler.plugins.pbspro:PbsproScheduler',
                'torque = aiida.scheduler.plugins.torque:TorqueScheduler',
            ],
            'aiida.transports': [
                'ssh = aiida.transport.plugins.ssh:SshTransport',
                'local = aiida.transport.plugins.local:LocalTransport',
            ],
            'aiida.workflows': [],
            'aiida.tools.dbexporters': [
                'tcod = aiida.tools.dbexporters.tcod'
            ],
            'aiida.tests': [],
            'aiida.tools.dbimporters': [
                'cod = aiida.tools.dbimporters.cod',
                'icsd = aiida.tools.dbimporters.icsd',
                'mpod = aiida.tools.dbimporters.mpod',
                'nninc = aiida.tools.dbimporters.nninc',
                'oqmd = aiida.tools.dbimporters.oqmd',
                'pcod = aiida.tools.dbimporters.pcod',
                'tcod = aiida.tools.dbimporters.tcod'
            ]
        },
        scripts=['bin/runaiida'],
        long_description=open(path.join(aiida_folder, 'README.rst')).read(),
    )

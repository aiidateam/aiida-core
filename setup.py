# -*- coding: utf-8 -*-
from os import path
from setuptools import setup, find_packages
from setup_requirements import install_requires, extras_require, dependency_links

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."



if __name__ == '__main__':
    # Get the version number
    aiida_folder = path.split(path.abspath(__file__))[0]
    fname = path.join(aiida_folder, 'aiida', '__init__.py')
    with open(fname) as aiida_init:
        ns = {}
        exec(aiida_init.read(), ns)
        aiida_version = ns['__version__']

    bin_folder = path.join(aiida_folder, 'bin')
    setup(
        name='aiida',
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
        dependency_links=dependency_links,
        packages=find_packages(),
        entry_points={
           'console_scripts': [
               'verdi=aiida.cmdline.verdilib:run'
            ],
           # following are AiiDA plugin entry points:
           'aiida.calculations': [
               'simpleplugins.templatereplacer = aiida.orm.calculation.job.simpleplugins.templatereplacer:TemplatereplacerCalculation',
               'quantumespresso.pw = aiida.orm.calculation.job.quantumespresso.pw:PwCalculation',
               'quantumespresso.cp = aiida.orm.calculation.job.quantumespresso.cp:CpCalculation',
               'quantumespresso.pwimmigrant = aiida.orm.calculation.job.quantumespresso.pwimmigrant:PwimmigrantCalculation',
               'nwchem.basic = aiida.orm.calculation.job.nwchem.basic:BasicCalculation',
               'nwchem.pymatgen = aiida.orm.calculation.job.nwchem.nwcpymatgen:NwcpymatgenCalculation',
               'codtools.ciffilter = aiida.orm.calculation.job.codtools.ciffilter:CiffilterCalculation',
               'codtools.cifcellcontents = aiida.orm.calculation.job.codtools.cifcellcontents:CifcellcontentsCalculation',
               'codtools.cifcodcheck = aiida.orm.calculation.job.codtools.cifcodcheck:CifcodcheckCalculation',
               'codtools.cifcoddeposit = aiida.orm.calculation.job.codtools.cifcoddeposit:CifcoddepositCalculation',
               'codtools.cifcodnumbers = aiida.orm.calculation.job.codtools.cifcodnumbers:CifcodnumbersCalculation',
               'codtools.cifsplitprimitive = aiida.orm.calculation.job.codtools.cifsplitprimitive:CifsplitprimitiveCalculation',
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
              'simple = aiida.orm.data.simple:SimpleData',
              'singlefile = aiida.orm.data.singlefile:SinglefileData',
              'structure = aiida.orm.data.structure:StructureData',
              'upf = aiida.orm.data.upf:UpfData'
          ],
          'aiida.parsers': [
              'codtools.cifcellcontents = aiida.parsers.plugins.codtools.cifcellcontents:CifcellcontentsParser',
              'codtools.cifcodcheck = aiida.parsers.plugins.codtools.cifcodcheck:CifcodcheckParser',
              'codtools.cifcoddeposit = aiida.parsers.plugins.codtools.cifcoddeposit:CifcoddepositParser',
              'codtools.cifcodnumbers = aiida.parsers.plugins.codtools.cifcodnumbers:CifcodnumbersParser',
              'codtools.ciffilter = aiida.parsers.plugins.codtools.ciffilter:CiffilterParser',
              'codtools.cifsplitprimitive = aiida.parsers.plugins.codtools.cifsplitprimitive:CifsplitprimitiveParser',
              'nwchem.basic = aiida.parsers.plugins.nwchem.basic:BasicParser',
              'nwchem.basenwc = aiida.parsers.plugins.nwchem.__init__:BasenwcParser',
              'nwchem.pymatgen = aiida.parsers.plugins.nwchem.nwcpymatgen:NwcpymatgenParser',
              'quantumespresso.basicpw = aiida.parsers.plugins.quantumespresso.basicpw:BasicpwParser',
              'quantumespresso.cp = aiida.parsers.plugins.quantumespresso.cp:CpParser',
              'quantumespresso.pw = aiida.parsers.plugins.quantumespresso.pw:PwParser',
          ],
          'aiida.cmdline': [],
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
       },
      scripts=['bin/runaiida'],
      long_description=open(path.join(aiida_folder, 'README.rst')).read(),
   )

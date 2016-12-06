# -*- coding: utf-8 -*-

from os import path
from setuptools import setup, find_packages

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."

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
    author=__authors__,
    author_email='developers@aiida.net',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ],
    version=aiida_version,
    # Abstract dependencies.  Concrete versions are listed in
    # requirements.txt
    # See https://caremad.io/2013/07/setup-vs-requirement/ for an explanation
    # of the difference and
    # http://blog.miguelgrinberg.com/post/the-package-dependency-blues
    # for a useful discussion
    install_requires=[
        'python-dateutil~=2.4.0',
        'django==1.7.4',
        'django_extensions==1.5',
        'pytz==2014.10',
        'django-celery==3.1.16',
        'celery==3.1.17',
        'billiard==3.3.0.19',
        'anyjson==0.3.3',
        'six==1.9',
        'supervisor==3.1.3',
        'meld3==1.0.0',
        'numpy',
        'plum==0.4.3',
        'SQLAlchemy==1.0.12',
        'SQLAlchemy-Utils==0.31.2',
        'ujson==1.35',
        'enum34==1.1.2',
        'voluptuous==0.8.11',
        'aldjemy',
        'passlib',
        'validate_email',
        'click==6.6',
        'tabulate==0.7.5',
        'ete3==3.0.0b35',
    ],
    extras_require={
        'verdi_shell': ['ipython'],
        'ssh': [
            'paramiko==1.15.2',
            'ecdsa==0.13',
            'pycrypto==2.6.1',
        ],
        'REST': [
            'django-tastypie==0.12.1',
            'python-mimeparse==0.1.4',
        ],
    },
    dependency_links=[
        'https://bitbucket.org/aiida_team/plum/get/v0.4.3.zip#egg=plum-0.4.3',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'verdi=aiida.cmdline.verdilib:run'
        ],
        # following are AiiDA plugin entry points:
        'aiida.calculations': [],
        'aiida.parsers': [],
        'aiida.cmdline': [],
        'aiida.schedulers': [],
        'aiida.transports': [],
        'aiida.workflows': [],
    },
    scripts=['bin/runaiida'],
    long_description=open(path.join(aiida_folder, 'README.rst')).read(),
)

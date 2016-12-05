# -*- coding: utf-8 -*-
import os

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

# Get the version number
aiida_folder = os.path.split(os.path.abspath(__file__))[0]
fname = os.path.join(aiida_folder, 'aiida', '__init__.py')
with open(fname) as aiida_init:
    ns = {}
    exec (aiida_init.read(), ns)
    aiida_version = ns['__version__']

if os.path.exists('CHANGELOG_EPFL.txt'):
    # EPFL version
    aiida_name = 'aiida-epfl'
    aiida_license = 'MIT and EPFL licenses, see LICENSE.txt'
else:
    aiida_name = 'aiida'
    aiida_license = 'MIT license, see LICENSE.txt'

bin_folder = os.path.join(aiida_folder, 'bin')
setup(
    name=aiida_name,
    url='http://www.aiida.net/',
    license=aiida_license,
    version=aiida_version,
    # Abstract dependencies.  Concrete versions are listed in
    # requirements.txt
    # See https://caremad.io/2013/07/setup-vs-requirement/ for an explanation
    # of the difference and
    # http://blog.miguelgrinberg.com/post/the-package-dependency-blues
    # for a useful dicussion
    install_requires=[
        'django', 'django_extensions', 'pytz', 'django-celery',
        'celery', 'billiard', 'anyjson', 'six', 'supervisor',
        'meld3', 'paramiko', 'ecdsa', 'pycrypto', 'numpy', 'django-tastypie',
        'python-dateutil', 'python-mimeparse', 'plum', 'enum34', 'voluptuous',
        'click', 'ujson'
    ],
    packages=find_packages(),
    scripts=[os.path.join(bin_folder, f) for f in os.listdir(bin_folder)
             if not os.path.isdir(os.path.join(bin_folder, f))],
    long_description=open(os.path.join(aiida_folder, 'README.rst')).read(),
)

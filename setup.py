# -*- coding: utf-8 -*-
import os

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Giovanni Pizzi, Martin Uhrin"

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
    name='aiida',
    url='http://www.aiida.net/',
    license='MIT licence, see LICENCE.txt',
    version="0.5.0",
    # Abstract dependencies.  Concrete versions are listed in
    # requirements.txt
    # See https://caremad.io/2013/07/setup-vs-requirement/ for an explanation
    # of the difference and
    # http://blog.miguelgrinberg.com/post/the-package-dependency-blues
    # for a useful dicussion
    install_requires=[
        'django', 'django_extensions', 'pytz', 'django-celery',
        'celery', 'kombu', 'billiard', 'amqp', 'anyjson', 'six', 'supervisor',
        'meld3', 'paramiko', 'ecdsa', 'pycrypto', 'numpy', 'django-tastypie',
        'python-dateutil', 'python-mimeparse',
        ],
    packages=find_packages(),
    scripts=[os.path.join("bin", f) for f in os.listdir("bin")
             if not os.path.isdir(os.path.join("bin", f))],
    long_description=open('README.rst').read(),
)


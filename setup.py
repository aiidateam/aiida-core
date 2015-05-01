import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
    name='aiida',
    url='http://www.aiida.net/',
    license='MIT licence, see LICENCE.txt',
    version="0.4.1",
    # Abstract dependencies.  Concrete versions are listed in
    # requirements.txt
    # See https://caremad.io/2013/07/setup-vs-requirement/ for an explanation
    # of the difference
    install_requires=[
        'django', 'django_extensions', 'pytz', 'django-celery',
        'celery', 'kombu', 'billiard', 'amqp', 'anyjson', 'six', 'supervisor',
        'meld3', 'psycopg2', 'pysqlite', 'paramiko', 'ecdsa', 'pycrypto',
        'numpy', 'django-tastypie', 'python-dateutil', 'python-mimeparse',
        ],
    packages=find_packages(),
    scripts=[os.path.join("bin", f) for f in os.listdir("bin")
             if not os.path.isdir(os.path.join("bin", f))],
    long_description=open('README.rst').read(),
)


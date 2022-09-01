# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os
import sys

import aiida
from aiida.manage.configuration import load_documentation_profile

# Load the dummy profile for sphinx autodoc to use when loading modules
load_documentation_profile()

# -- General configuration -----------------------------------------------------

# General information about the project.
project = 'AiiDA'
author = 'The AiiDA team.'
copyright = (
    '2014-2020, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE '
    '(Theory and Simulation of Materials (THEOS) and '
    'National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), '
    'Switzerland and ROBERT BOSCH LLC, USA. All rights reserved'
)
# The short X.Y version.
version = '.'.join(aiida.__version__.split('.')[:2])
# The full version, including alpha/beta/rc tags.
release = aiida.__version__

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    'datatypes/**',
    'developer_guide/**',
    'get_started/**',
    'howto/installation_more/index.rst',
    'import_export/**',
    'internals/global_design.rst',
    'internals/orm.rst',
    'scheduler/index.rst',
    'topics/daemon.rst',
    'working_with_aiida/**',
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# Enable labeling for figures
numfig = True

# -- Extension configuration -----------------------------------------------------

extensions = [
    'myst_nb', 'sphinx.ext.intersphinx', 'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.viewcode',
    'sphinx.ext.coverage', 'sphinx.ext.mathjax', 'sphinx.ext.ifconfig', 'sphinx.ext.todo',
    'IPython.sphinxext.ipython_console_highlighting', 'IPython.sphinxext.ipython_directive', 'aiida.sphinxext',
    'sphinx_design', 'sphinx_copybutton', 'sphinxext.rediraffe', 'notfound.extension', 'sphinx_sqlalchemy'
]

intersphinx_mapping = {
    'aep': ('https://aep.readthedocs.io/en/latest/', None),
    'click': ('https://click.palletsprojects.com/', None),
    'flask': ('http://flask.pocoo.org/docs/latest/', None),
    'flask_restful': ('https://flask-restful.readthedocs.io/en/latest/', None),
    'kiwipy': ('https://kiwipy.readthedocs.io/en/latest/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'plumpy': ('https://plumpy.readthedocs.io/en/latest/', None),
    'python': ('https://docs.python.org/3', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/14/', None),
}

todo_include_todos = False
ipython_mplbackend = ''

myst_enable_extensions = ['colon_fence', 'deflist']
nb_merge_streams = True

# -- Options for HTML output ---------------------------------------------------

# see: https://pydata-sphinx-theme.readthedocs.io/en/latest/user_guide/configuring.html
html_theme = 'pydata_sphinx_theme'
html_theme_options = {
    'external_links': [{
        'url': 'http://www.aiida.net/',
        'name': 'AiiDA Home'
    }],
    'github_url': 'https://github.com/aiidateam/aiida-core',
    'twitter_url': 'https://twitter.com/aiidateam',
    'use_edit_page_button': True,
}
html_context = {
    'github_user': 'aiidateam',
    'github_repo': 'aiida-core',
    'github_version': 'main',
    'doc_path': 'docs/source',
}

notfound_urls_prefix = '/projects/aiida-core/en/latest/'

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = 'images/logo_aiida_docs.png'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ['aiida-custom.css']
rediraffe_redirects = 'redirects.txt'

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

copybutton_selector = 'div:not(.no-copy)>div.highlight pre'
copybutton_prompt_text = r'>>> |\.\.\. |(?:\(.*\) )?\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: '
copybutton_prompt_is_regexp = True

linkcheck_ignore = [
    r'http://localhost:\d+/',
    r'http://127.0.0.1:\d+/',
    r'http://www.wannier.org/support/',
    r'https://github.com/aiidateam/aiida-diff/blob/92c61bdcc2db201d69da4d8b83a2b3f5dd529bf1/aiida_diff/data/__init__.py#L14-L20',
    r'https://github.com/aiidateam/aiida-core/pull/\d+',
]

# -- API documentation ---------------------------------------------------


def run_apidoc(_):
    """Runs sphinx-apidoc when building the documentation.

    Needs to be done in conf.py in order to include the APIdoc in the
    build on readthedocs.

    See also https://github.com/rtfd/readthedocs.org/issues/1139
    """
    source_dir = os.path.abspath(os.path.dirname(__file__))
    apidoc_dir = os.path.join(source_dir, 'reference', 'apidoc')
    package_dir = os.path.join(source_dir, os.pardir, os.pardir, 'aiida')
    exclude_api_patterns = [
        os.path.join(package_dir, 'storage', 'psql_dos', 'migrations', 'versions'),
    ]

    # In #1139, they suggest the route below, but for me this ended up
    # calling sphinx-build, not sphinx-apidoc
    #from sphinx.apidoc import main
    #main([None, '-e', '-o', apidoc_dir, package_dir, '--force'])

    import subprocess
    cmd_path = 'sphinx-apidoc'
    if hasattr(sys, 'real_prefix'):  # Check to see if we are in a virtualenv
        # If we are, assemble the path manually
        cmd_path = os.path.abspath(os.path.join(sys.prefix, 'bin', 'sphinx-apidoc'))

    options = [
        package_dir,
        *exclude_api_patterns,
        '-o',
        apidoc_dir,
        '--private',
        '--force',
        '--no-headings',
        '--module-first',
        '--no-toc',
        '--maxdepth',
        '4',
    ]

    # See https://stackoverflow.com/a/30144019
    env = os.environ.copy()
    env['SPHINX_APIDOC_OPTIONS'
        ] = 'members,special-members,private-members,undoc-members,show-inheritance,ignore-module-all'
    subprocess.check_call([cmd_path] + options, env=env)


# Warnings to ignore when using the -n (nitpicky) option
nitpicky = True
with open('nitpick-exceptions', 'r') as handle:
    nitpick_ignore = [
        tuple(line.strip().split(None, 1)) for line in handle.readlines() if line.strip() and not line.startswith('#')
    ]

# -- Non-html output formats options ---------------------------------------------------

htmlhelp_basename = 'aiidadoc'

latex_documents = [
    ('index', 'aiida.tex', 'AiiDA documentation', author.replace(',', r'\and'), 'manual'),
]

man_pages = [('index', 'aiida', 'AiiDA documentation', [author], 1)]

texinfo_documents = [
    (
        'index', 'aiida', 'AiiDA documentation', author, 'aiida',
        'Automated Interactive Infrastructure and Database for Computational Science', 'Miscellaneous'
    ),
]

epub_title = 'AiiDA'
epub_author = author
epub_publisher = author
epub_copyright = copyright

# -- Local extension --------------------------------------------------
from sphinx.addnodes import pending_xref
from sphinx.application import Sphinx
from sphinx.transforms import SphinxTransform


def setup(app: Sphinx):
    if os.environ.get('RUN_APIDOC', None) != 'False':
        app.connect('builder-inited', run_apidoc)
    app.add_transform(AutodocAliases)


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
    'ProcessNode': 'aiida.orm.nodes.process.process.ProcessNode',
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

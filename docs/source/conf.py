# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import inspect
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
myst_heading_anchors = 3
nb_execution_show_tb = 'READTHEDOCS' in os.environ
nb_merge_streams = True
nb_mime_priority_overrides = [
    ('gettext', 'application/vnd.jupyter.widget-view+json', 0),
    ('gettext', 'application/javascript', 10),
    ('gettext', 'text/html', 20),
    ('gettext', 'image/svg+xml', 30),
    ('gettext', 'image/png', 40),
    ('gettext', 'image/jpeg', 50),
    ('gettext', 'text/markdown', 60),
    ('gettext', 'text/latex', 70),
    ('gettext', 'text/plain', 80),
]

# -- Options for HTML output ---------------------------------------------------

# see: https://pydata-sphinx-theme.readthedocs.io/en/latest/user_guide/configuring.html
html_theme = 'pydata_sphinx_theme'
html_theme_options = {
    'use_edit_page_button': True,
    'icon_links': [
        {
            'name': 'AiiDA',
            'url': 'http://aiida.net',
            'icon': '_static/logo-aiida-gray.svg',
            'type': 'local',
        },
        {
            'name': 'Discourse',
            'url': 'https://aiida.discourse.group',
            'icon': 'fa-brands fa-discourse',
            'type': 'fontawesome',
        },
        {
            'name': 'GitHub',
            'url': 'https://www.github.com/aiidateam/aiida-core',
            'icon': 'fa-brands fa-square-github',
            'type': 'fontawesome',
        },
        {
            'name': 'Twitter',
            'url': 'https://www.twitter.com/aiidateam',
            'icon': 'fa-brands fa-twitter-square',
            'type': 'fontawesome',
        },
    ],
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
from sphinx.domains.python import PythonDomain
from sphinx.environment import BuildEnvironment
from sphinx.transforms import SphinxTransform


def setup(app: Sphinx):
    if os.environ.get('RUN_APIDOC', None) != 'False':
        app.connect('builder-inited', run_apidoc)
    app.add_transform(AutodocAliases)
    app.connect('env-updated', add_python_aliases)


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
    'CalcJobNode': 'aiida.orm.nodes.process.calculation.calcjob.CalcJobNode',
    'BackendAuthInfo': 'aiida.orm.implementation.authinfos.BackendAuthInfo',
    'BackendComment': 'aiida.orm.implementation.comments.BackendComment',
    'BackendComputer': 'aiida.orm.implementation.computers.BackendComputer',
    'BackendGroup': 'aiida.orm.implementation.groups.BackendGroup',
    'BackendLog': 'aiida.orm.implementation.logs.BackendLog',
    'BackendNode': 'aiida.orm.implementation.nodes.BackendNode',
    'BackendUser': 'aiida.orm.implementation.users.BackendUser',
}


def add_python_aliases(app: Sphinx, env: BuildEnvironment) -> None:
    """Add aliases to the python domain.

    These will also be added to the objects.inv inventory file,
    for other projects to reference.
    """
    py: PythonDomain = env.get_domain('py')

    shorthands = {}
    for modname, module in inspect.getmembers(aiida, inspect.ismodule):
        for name in getattr(module, '__all__', []):
            obj = getattr(module, name)
            if hasattr(obj, '__module__'):
                shorthands[f'{obj.__module__}.{name}'] = f'aiida.{modname}.{name}'

    updates = {}
    for name, obj in py.objects.items():
        if name in shorthands:
            updates[shorthands[name]] = obj._replace(aliased=True)
            continue
        for original, new in shorthands.items():
            if name.startswith(original + '.'):
                updates[name.replace(original, new)] = obj._replace(aliased=True)
                break
    py.objects.update(updates)


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
            if node.get('reftarget').startswith('t.'):
                node['reftarget'] = 'typing.' + node.get('reftarget')[2:]
            elif node.get('reftarget') in autodoc_aliases_typing:
                node['reftarget'] = autodoc_aliases_typing[node.get('reftarget')]

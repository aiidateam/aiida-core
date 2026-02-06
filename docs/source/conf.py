###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os

import aiida

# imports required for docs/source/reference/api/public.rst
from aiida import (  # noqa: F401
    cmdline,
    common,
    engine,
    manage,
    orm,
    parsers,
    plugins,
    schedulers,
    tools,
    transports,
)
from aiida.cmdline.params import arguments, options  # noqa: F401

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
    'developer_guide/**',
    'import_export/**',
    'internals/global_design.rst',
    'reference/apidoc/**',
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# Enable labeling for figures
numfig = True

# -- Extension configuration -----------------------------------------------------

extensions = [
    'myst_nb',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.todo',
    'IPython.sphinxext.ipython_console_highlighting',
    'IPython.sphinxext.ipython_directive',
    'aiida.sphinxext',
    'sphinx_design',
    'sphinx_copybutton',
    'sphinxext.rediraffe',
    'notfound.extension',
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
myst_heading_anchors = 4

# MyST-NB configuration for executing tutorial notebooks
nb_execution_mode = os.environ.get('MYST_NB_EXECUTION_MODE', 'auto')
nb_execution_show_tb = 'READTHEDOCS' in os.environ
nb_execution_timeout = 180  # 3 minutes per cell
nb_merge_streams = True
nb_execution_excludepatterns = []  # Can exclude specific files if needed
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
            'icon': 'fa-brands fa-square-x-twitter',
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

# This is to tell search engines to index only stable and latest version
html_extra_path = ['robots.txt']

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

# Warnings to ignore when using the -n (nitpicky) option
nitpicky = True
with open('nitpick-exceptions', 'r') as handle:
    nitpick_ignore = [
        tuple(line.strip().split(None, 1)) for line in handle.readlines() if line.strip() and not line.startswith('#')
    ]

# Regex patterns to ignore for references that are not documented (e.g., autodoc is deactivated)
nitpick_ignore_regex = [
    (r'py:.*', r'aiida.*'),
]

# -- Non-html output formats options ---------------------------------------------------

htmlhelp_basename = 'aiidadoc'

latex_documents = [
    ('index', 'aiida.tex', 'AiiDA documentation', author.replace(',', r'\and'), 'manual'),
]

man_pages = [('index', 'aiida', 'AiiDA documentation', [author], 1)]

texinfo_documents = [
    (
        'index',
        'aiida',
        'AiiDA documentation',
        author,
        'aiida',
        'Automated Interactive Infrastructure and Database for Computational Science',
        'Miscellaneous',
    ),
]

epub_title = 'AiiDA'
epub_author = author
epub_publisher = author
epub_copyright = copyright

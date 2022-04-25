# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
An IPython extension that provides a magic command to load
basic aiida commands.

This makes it much easier to start.

Produces output in:

* Plaintext (IPython [qt]console)
* HTML (IPython notebook, ``nbconvert --to html``, ``--to slides``)
* JSON (IPython notebook ``.ipynb`` files)
* LaTeX (e.g. ``ipython nbconvert example.ipynb --to LaTeX --post PDF``)


Notes on how to load it at start:
https://ipython.org/ipython-doc/3/config/intro.html

Usage
======

.. sourcecode:: ipython

   In [1]: %load_ext aiida_magic

   In [2]: %aiida
"""
import json
import shlex

from IPython import get_ipython, version_info
from IPython.core import magic


def add_to_ns(local_ns, name, obj):
    """
    Add a new variable with name ``name`` and value ``obj`` to the
    namespace ``local_ns``, optionally showing a warning if we are
    hiding an existing variable.

    .. todo:: implement the warning.

    Example::

        # assuming that local_ns is a dictionary, e.g. from locals()
        import sys
        add_to_ns(local_ns, 'sys', sys)
    """
    if name in local_ns:
        pass
    local_ns[name] = obj


@magic.magics_class
class AiiDALoaderMagics(magic.Magics):
    """AiiDA magic loader."""

    @magic.needs_local_scope
    @magic.line_magic
    def verdi(self, line='', local_ns=None):  # pylint: disable=no-self-use,unused-argument
        """Run the AiiDA command line tool, using the currently loaded configuration and profile."""
        from aiida.cmdline.commands.cmd_verdi import verdi
        from aiida.common import AttributeDict
        from aiida.manage import get_config, get_profile
        config = get_config()
        profile = get_profile()
        obj = AttributeDict({'config': config, 'profile': profile})
        return verdi(shlex.split(line), prog_name='%verdi', obj=obj, standalone_mode=False)  # pylint: disable=too-many-function-args,unexpected-keyword-arg

    @magic.needs_local_scope
    @magic.line_magic
    def aiida(self, line='', local_ns=None):
        """Load AiiDA in ipython (checking if it was already loaded), and
        inserts in the namespace the main AiiDA classes (the same that are
        loaded in ``verdi shell``.

        Usage::

            %aiida [optional parameters]

        .. todo:: implement parameters, e.g. for the profile to load.
        """
        # pylint: disable=unused-argument,attribute-defined-outside-init
        from aiida.cmdline.utils.shell import get_start_namespace
        from aiida.manage.configuration import load_profile

        self.is_warning = False
        lcontent = line.strip()
        if lcontent:
            profile = load_profile(lcontent)
        else:
            profile = load_profile()

        self.current_state = f'Loaded AiiDA DB environment - profile name: {profile.name}.'

        user_ns = get_start_namespace()
        for key, value in user_ns.items():
            add_to_ns(local_ns, key, value)

        return self

    def _repr_json_(self):
        """
        Output in JSON format.
        """
        obj = {'current_state': self.current_state}
        if version_info[0] >= 3:
            return obj

        return json.dumps(obj)

    def _repr_html_(self):
        """
        Output in HTML format.
        """
        html = '<p>'
        if self.is_warning:
            html += '<strong>'
        html += self.current_state
        if self.is_warning:
            html += '</strong>'
        html += '</p>'

        return html

    def _repr_latex_(self):
        """
        Output in LaTeX format.
        """
        if self.is_warning:
            latex = '\\emph{%s}\n' % self.current_state
        else:
            latex = f'{self.current_state}\n'

        return latex

    def _repr_pretty_(self, pretty_print, cycle):  # pylint: disable=unused-argument
        """
        Output in text format.
        """
        if self.is_warning:
            warning_str = '** '
        else:
            warning_str = ''
        text = f'{warning_str}{self.current_state}\n'

        pretty_print.text(text)


def load_ipython_extension(ipython):
    """
    Registers the %aiida IPython extension.

    .. deprecated:: v3.0.0
        Use :py:func:`~aiida.tools.ipython.ipython_magics.register_ipython_extension` instead.
    """
    register_ipython_extension(ipython)


def register_ipython_extension(ipython=None):
    """
    Registers the %aiida IPython extension.

    The %aiida IPython extension provides the same environment as the `verdi shell`.

    :param ipython: InteractiveShell instance. If omitted, the global InteractiveShell is used.

    """
    if ipython is None:
        ipython = get_ipython()

    ipython.register_magics(AiiDALoaderMagics)

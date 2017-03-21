# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
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
import IPython
from IPython.core.magic import (magics_class, line_magic, Magics, 
                                needs_local_scope)


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
        # TODO: print warning, or raise
        pass
    local_ns[name] = obj
    
@magics_class
class AiiDALoaderMagics(Magics):

    @needs_local_scope
    @line_magic
    def aiida(self, line='', local_ns=None):
        """Load AiiDA in ipython (checking if it was already loaded), and
        inserts in the namespace the main AiiDA classes (the same that are
        loaded in ``verdi shell``.

        Usage::

            %aiida [optional parameters]
        
        .. todo:: implement parameters, e.g. for the profile to load.
        """
        import aiida
        
        from aiida import is_dbenv_loaded, load_dbenv
                
        self.is_warning = False
        if is_dbenv_loaded():
            self.current_state = "Note! AiiDA DB environment already loaded! I do not reload it again."
            self.is_warning = True
        else:
            load_dbenv()
            self.current_state = "Loaded AiiDA DB environment."

        from aiida.cmdline.commands.shell import Shell
        user_ns = Shell().get_start_namespace()
        for k, v in user_ns.iteritems():
            add_to_ns(local_ns, k, v)
            
        return self

    def _repr_json_(self):
        """
        Output in JSON format.
        """
        obj = {
            'current_state': self.current_state}
        if IPython.version_info[0] >= 3:
            return obj
        else:
            return json.dumps(obj)

    def _repr_html_(self):
        """
        Output in HTML format.
        """
        html = "<p>"
        if self.is_warning:
            html += "<strong>"
        html += self.current_state
        if self.is_warning:
            html += "</strong>"
        html += "</p>"

        return html

    def _repr_latex_(self):
        """
        Output in LaTeX format.
        """
        if self.is_warning:
            latex = "\\emph{%s}\n" % self.current_state
        else:
            latex = "%s\n" % self.current_state

        return latex

    def _repr_pretty_(self, pp, cycle):
        """
        Output in text format.
        """
        if self.is_warning:
            warning_str = "** "
        else:
            warning_str = ""
        text = "%s%s\n" % (warning_str, self.current_state)

        pp.text(text)

        
def load_ipython_extension(ipython):
    """
    Triggers the load of all the AiiDA magic commands.
    """
    ipython.register_magics(AiiDALoaderMagics)

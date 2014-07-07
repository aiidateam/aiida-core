# -*- coding: utf-8 -*-
import importlib

import aiida.common
from aiida.common.exceptions import MissingPluginError

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

logger = aiida.common.aiidalogger.getChild('pluginloader')

def get_class_typestring(type_string):
    """
    Given the type string, return three strings: the first one is 
    one of the first-level classes that the Node can be:
    "node", "calculation", "code", "data".
    The second string is the one that can be passed to the DataFactory or
    CalculationFactory (or an empty string for nodes and codes);
    the third one is the name of the python class that would be loaded.
    """
    from aiida.common.exceptions import DbContentError
    
    if type_string == "":
        return ("node", "")
    else:
        pieces = type_string.split('.')
        if pieces[-1]:
            raise DbContentError("The type string does not end with a dot")
        if len(pieces) < 3:
            raise DbContentError("Not enough parts in the type string")
        return pieces[0], ".".join(pieces[1:-2]), pieces[-2]
        

def _existing_plugins_with_module(base_class, plugins_module_path,
                                  pkgname, basename, max_depth):
    """
        Recursive function to return the existing plugins within a given module.
        
        Args:
        base_class
            Identify all subclasses of the base_class
        plugins_module
            a python module object (*not* a string) within which to look for a plugin.
        max_depth
            (default=5) Maximum depth (of nested modules) to be used when
            looking for plugins
        Return:
            a list of valid strings that can be used using a Factory or with
            load_plugin.
    """
    import pkgutil
    import os
    
    if max_depth == 0:
        return []
    else:
        retlist = _find_module(base_class, pkgname, basename) 
        
        for _, name, ismod in pkgutil.walk_packages([plugins_module_path]):
            if ismod:
                retlist += _existing_plugins_with_module(
                     base_class, os.path.join(plugins_module_path,name),
                     "{}.{}".format(pkgname, name),
                     "{}.{}".format(basename, name) if basename else name,
                     max_depth-1)

            # This has to be done anyway, for classes in the __init__ file.
            this_pkgname = "{}.{}".format(pkgname, name)
            this_basename = "{}.{}".format(basename, name) if basename else name

            retlist += _find_module(base_class, this_pkgname, this_basename)

                
        return list(set(retlist))

def _find_module(base_class, pkgname, this_basename):
    """
    Given a base class object, looks for its subclasses inside the package
    with name pkgname (must be importable), and prepends to the class name
    the string 'this_basename'.
    
    Return a list of valid strings, acceptable by the *Factory functions.
    Does not return the class itself.
    
    If the name of the class complies with the syntax
    AaaBbb
    where Aaa is the capitalized name of the containing module (aaa), and
    Bbb is base_class.__name__, then only 'aaa' is returned instead of
    'aaa.AaaBbb', to have a shorter name that is anyway accepted by the *Factory
    functions. 
    """
    import inspect

    retlist = []
            
    #print ' '*(5-max_depth), '>', pkgname
    #print ' '*(5-max_depth), ' ', this_basename

    pkg = importlib.import_module(pkgname)
    for k, v in pkg.__dict__.iteritems():
        if (inspect.isclass(v) and # A class
            v != base_class and # Not the class itself
            issubclass(v, base_class) and # a proper subclass
            pkgname == v.__module__):   # We are importing it from its
                                        # module: avoid to import it
                                        # from another module, if it
                                        # was simply imported there
            # Try to return the shorter name if the subclass name
            # has the correct pattern, as expected by the Factory
            # functions
            if k == "{}{}".format(
              pkgname.rpartition('.')[2].capitalize(),
              base_class.__name__):
                retlist.append(this_basename)
            else:
                retlist.append(
                   ("{}.{}".format(this_basename, k) if this_basename
                    else k))
        #print ' '*(5-max_depth), ' ->', "{}.{}".format(this_basename, k)
    return retlist        

def existing_plugins(base_class, plugins_module_name, max_depth=5):
    """
    Return a list of strings of valid plugins.
    
    Args:
        base_class
            Identify all subclasses of the base_class
        plugins_module_name
            a string with the full module name separated with dots
            that points to the folder with plugins. It must be importable by python.
        max_depth
            (default=5) Maximum depth (of nested modules) to be used when
            looking for plugins
    
    TODO: unify this function, the load_plugin function, and possibly think to
        a caching/registering method for plugins.
    """
    try:
        pluginmod = importlib.import_module(plugins_module_name)
    except ImportError:
        raise MissingPluginError("Unable to load the plugin module {}".format(
            plugins_module_name))

    return _existing_plugins_with_module(base_class,
                                         pluginmod.__path__[0],
                                         plugins_module_name,
                                         "",
                                         max_depth)

def load_plugin(base_class, plugins_module, plugin_type):
    """
    Load a specific plugin for the given base class. 

    This is general and works for any plugin used in AiiDA.

    NOTE: actually, now plugins_module and plugin_type are joined with a dot,
        and the plugin is retrieved splitting using the last dot of the resulting
        string.
    TODO: understand if it is probably better to join the two parameters above
        to a single one.

    Args:
        base_class
            the abstract base class of the plugin.
        plugins_module
            a string with the full module name separated with dots
            that points to the folder with plugins. It must be importable by python.
        plugin_type
            the name of the plugin.
            
    Return: 
        the class of the required plugin.

    Raise:
        MissingPluginError if the plugin cannot be loaded

    Example:
       plugin_class = load_plugin(
           aiida.transport.Transport,'aiida.transport.plugins','ssh.SshTransport')

       and plugin_class will be the class 'aiida.transport.plugins.ssh.SshTransport'
    """

    module_name = ".".join([plugins_module,plugin_type])
    real_plugin_module, plugin_name = module_name.rsplit('.',1)
    
    try:
        pluginmod = importlib.import_module(real_plugin_module)
    except ImportError:
        raise MissingPluginError("Unable to load the plugin module {}".format(
            real_plugin_module))

    try:
        pluginclass = pluginmod.__dict__[plugin_name] 
    except KeyError:
        raise MissingPluginError("Unable to load the class {} within {}".format(
            plugin_name, real_plugin_module))

    
    try:
        if issubclass(pluginclass, base_class):
            return pluginclass
        else:
            # Quick way of going into the except case
            err_msg = "{} is not a subclass of {}".format(
                module_name, base_class.__name__)
            raise MissingPluginError(err_msg)
    except TypeError:
        # This happens when we pass a non-class to issubclass; 
        err_msg = "{} is not a class".format(
            module_name)
        raise MissingPluginError(err_msg)


def BaseFactory(module, base_class, base_modname):
    """
    Return a given subclass of Calculation, loading the correct plugin.
    
    Args:
        module: a string with the module of the plugin to load, e.g.
          'quantumespresso.pw'.
        base_class: a base class from which the returned class should inherit.
           e.g.: Calculation
        base_modname: a basic module name, under which the module should be
            found. E.g., 'aiida.orm.calculation'.
        
    In the above case, the code will first look for a pw subclass of Calculation
    inside the quantumespresso module. Lacking such a class, it will try to look
    for a 'PwCalculation' inside the quantumespresso.pw module.
    In the latter case, the plugin class must have a specific name and be
    located in a specific file:
    if for instance plugin_name == 'ssh' and base_class.__name__ == 'Transport',
    thend there must be a class named 'SshTransport' which is a subclass of base_class
    in a file 'ssh.py' in the plugins_module folder.
    """   
    try:
        return load_plugin(base_class, base_modname, module)
    except MissingPluginError as e1:
        # Automatically add subclass name and try again
        mname = module.rpartition('.')[2].capitalize() + base_class.__name__
        new_module = module+ '.' +mname
        try:
            return load_plugin(base_class, base_modname, new_module)
        except MissingPluginError as e2:
            err_msg = ("Neither {} or {} could be loaded from {}. "
                       "Error messages were: '{}', '{}'").format(
                module, new_module, base_modname, e1, e2)
            raise MissingPluginError(err_msg)
        

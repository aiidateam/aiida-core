# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import importlib

import aiida.common
from aiida.common.exceptions import MissingPluginError


logger = aiida.common.aiidalogger.getChild('pluginloader')


def from_type_to_pluginclassname(typestr):
    """
    Return the string to pass to the load_plugin function, starting from
    the 'type' field of a Node.
    """
    # Fix for base class
    from aiida.common.exceptions import DbContentError
    if typestr == "":
        typestr = "node.Node."
    if not typestr.endswith("."):
        raise DbContentError("The type name '{}' is not valid!".format(
            typestr))
    return typestr[:-1]  # Strip final dot

def get_query_type_string(plugin_type_string):
    """
    Receives a plugin_type_string, an attribute of subclasses of Node.
    Checks whether it is a valid type_string and manipulates the string
    to return a string that in a query returns all instances of a class and
    all instances of subclasses.

    :param plugin_type_string: The plugin_type_string

    :returns: the query_type_string
    """
    from aiida.common.exceptions import DbContentError, InputValidationError
    if not isinstance(plugin_type_string, basestring):
        raise InputValidationError("You have to pass as argument")
    # First case, an empty string for Node:
    if plugin_type_string == '':
        query_type_string = ''
    # Anything else should have baseclass.Class., so at least 2 dots
    # and end with a dot:
    elif not(plugin_type_string.endswith('.')) or plugin_type_string.count('.') == 1:
        raise DbContentError(
                "The type name '{}' is not valid!".format(plugin_type_string)
            )
    else:
        query_type_string = '{}.'.format('.'.join(plugin_type_string.split('.')[:-2]))
    return query_type_string


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
                                  pkgname, basename, max_depth, suffix=None):
    """
        Recursive function to return the existing plugins within a given module.

        :param base_class: Identify all subclasses of the base_class
        :param plugins_module_path: The path to the folder with the plugins
        :param pkgname: The name of the package in which you want to search
        :param basename: The basename of the plugin (sub)class. See also documentation
            of ``find_module``.
        :param max_depth: Maximum depth (of nested modules) to be used when
            looking for plugins
        :param suffix: The suffix that is appended to the basename when looking
            for the (sub)class name. If not provided (or None), use the base
            class name.
        :return: a list of valid strings that can be used using a Factory or with
            load_plugin.
    """
    import pkgutil
    import os

    if max_depth == 0:
        return []
    else:
        retlist = _find_module(base_class, pkgname, basename, suffix)

        prefix = pkgname + '.'
        for _, name, ismod in pkgutil.walk_packages([plugins_module_path], prefix=prefix):
            plugin_name = name[len(prefix):]
            if ismod:
                retlist += _existing_plugins_with_module(
                    base_class, os.path.join(plugins_module_path, plugin_name),
                    name,
                    "{}.{}".format(basename, plugin_name) if basename else plugin_name,
                    max_depth - 1, suffix=suffix)

            # This has to be done anyway, for classes in the __init__ file.
            this_basename = "{}.{}".format(basename, plugin_name) if basename else plugin_name

            retlist += _find_module(base_class, name, this_basename, suffix)

        return list(set(retlist))


def _find_module(base_class, pkgname, this_basename, suffix=None):
    """
    Given a base class object, looks for its subclasses inside the package
    with name pkgname (must be importable), and prepends to the class name
    the string 'this_basename'.

    If the name of the class complies with the syntax
    AaaBbb
    where Aaa is the capitalized name of the containing module (aaa), and
    Bbb is base_class.__name__, then only 'aaa' is returned instead of
    'aaa.AaaBbb', to have a shorter name that is anyway accepted by the *Factory
    functions. If suffix is provided, this is used for comparison (the 'Bbb'
    string) rather than the base class name)

    :param base_class: Identify all subclasses of the base_class
    :param pkgname: The name of the package in which you want to search
    :param basename: The basename of the plugin (sub)class. See also documentation
        of ``find_module``.
    :param suffix: The suffix that is appended to the basename when looking
        for the (sub)class name. If not provided (or None), use the base
        class name.
    :return: a list of valid strings, acceptable by the *Factory functions.
       Does not return the class itself.
    """
    import inspect

    retlist = []

    # print ' '*(5-max_depth), '>', pkgname
    #print ' '*(5-max_depth), ' ', this_basename

    pkg = importlib.import_module(pkgname)
    for k, v in pkg.__dict__.iteritems():
        if (inspect.isclass(v) and  # A class
                    v != base_class and  # Not the class itself
                issubclass(v, base_class) and  # a proper subclass
                    pkgname == v.__module__):  # We are importing it from its
            # module: avoid to import it
            # from another module, if it
            # was simply imported there
            # Try to return the shorter name if the subclass name
            # has the correct pattern, as expected by the Factory
            # functions
            if suffix is None:
                actual_suffix = base_class.__name__
            else:
                actual_suffix = suffix

            if k == "{}{}".format(
                    pkgname.rpartition('.')[2].capitalize(),
                    actual_suffix):
                retlist.append(this_basename)
            else:
                retlist.append(
                    ("{}.{}".format(this_basename, k) if this_basename
                     else k))
                #print ' '*(5-max_depth), ' ->', "{}.{}".format(this_basename, k)
    return retlist


def existing_plugins(base_class, plugins_module_name, max_depth=5, suffix=None):
    """
    Return a list of strings of valid plugins.


    :param base_class: Identify all subclasses of the base_class
    :param plugins_module_name: a string with the full module name separated
        with dots that points to the folder with plugins.
        It must be importable by python.
    :param max_depth: Maximum depth (of nested modules) to be used when
            looking for plugins
    :param suffix: The suffix that is appended to the basename when looking
        for the (sub)class name. If not provided (or None), use the base
        class name.
    :return: a list of valid strings that can be used using a Factory or with
        load_plugin.
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
                                         max_depth, suffix)


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

    module_name = ".".join([plugins_module, plugin_type])
    real_plugin_module, plugin_name = module_name.rsplit('.', 1)


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


def BaseFactory(module, base_class, base_modname, suffix=None):
    """
    Return a given subclass of Calculation, loading the correct plugin.

    :example: If `module='quantumespresso.pw'`, `base_class=JobCalculation`,
      `base_modname = 'aiida.orm.calculation.job'`, and `suffix='Calculation'`,
      the code will first look for a pw subclass of JobCalculation
      inside the quantumespresso module. Lacking such a class, it will try to look
      for a 'PwCalculation' inside the quantumespresso.pw module.
      In the latter case, the plugin class must have a specific name and be
      located in a specific file:
      if for instance plugin_name == 'ssh' and base_class.__name__ == 'Transport',
      then there must be a class named 'SshTransport' which is a subclass of base_class
      in a file 'ssh.py' in the plugins_module folder.
      To create the class name to look for, the code will attach the string
      passed in the base_modname (after the last dot) and the suffix parameter,
      if passed, with the proper CamelCase capitalization. If suffix is not
      passed, the default suffix that is used is the base_class class name.

    :param module: a string with the module of the plugin to load, e.g.
          'quantumespresso.pw'.
    :param base_class: a base class from which the returned class should inherit.
           e.g.: JobCalculation
    :param base_modname: a basic module name, under which the module should be
            found. E.g., 'aiida.orm.calculation.job'.
    :param suffix: If specified, the suffix that the class name will have.
      By default, use the name of the base_class.
    """
    try:
        return load_plugin(base_class, base_modname, module)
    except MissingPluginError as e1:
        # Automatically add subclass name and try again
        if suffix is None:
            actual_suffix = base_class.__name__
        else:
            actual_suffix = suffix
        mname = module.rpartition('.')[2].capitalize() + actual_suffix
        new_module = module + '.' + mname
        try:
            return load_plugin(base_class, base_modname, new_module)
        except MissingPluginError as e2:
            err_msg = ("Neither {} or {} could be loaded from {}. "
                       "Error messages were: '{}', '{}'").format(
                module, new_module, base_modname, e1, e2)
            raise MissingPluginError(err_msg)


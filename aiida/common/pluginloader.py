import importlib

import aiida.common
from aiida.common.exceptions import MissingPluginError, InternalError

logger = aiida.common.aiidalogger.getChild('pluginloader')

def load_plugin(base_class, plugins_module, plugin_type):
    """
    Load a specific plugin for the given base class. 

    This is general and works for any plugin used in AiiDA.

    Args:
        base_class: the abstract base class of the plugin.
        plugins_module: a string with the full module name separated with dots
            that points to the folder with plugins. It must be importable by python.
        plugin_type: the name of the plugin.
    NOTE: actually, now plugins_module and plugin_type are joined with a dot,
        and the plugin is retrieved splitting using the last dot of the resulting
        string.
    TODO: understand if it is probably better to join the two parameters above
        to a single one.

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
        

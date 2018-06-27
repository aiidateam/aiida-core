from aiida.cmdline import delayed_load_node as load_node

def deposit_tcod(node, deposit_type, parameter_data=None, **kwargs):
    """
    Deposition plugin for TCOD.
    """
    from aiida.tools.dbexporters.tcod import deposit
    parameters = None
    if parameter_data is not None:
        from aiida.orm import DataFactory
        ParameterData = DataFactory('parameter')
        parameters = load_node(parameter_data, sub_class=ParameterData)
    return deposit(node, deposit_type, parameters, **kwargs)

# -*- coding: utf-8 -*-
"""Definition of modules that are to be automatically loaded for `verdi shell`."""

DEFAULT_MODULES_LIST = [
    ('aiida.orm', 'Node', 'Node'),
    ('aiida.orm', 'Calculation', 'Calculation'),
    ('aiida.orm', 'load_workflow', 'load_workflow'),
    ('aiida.orm', 'JobCalculation', 'JobCalculation'),
    ('aiida.orm', 'Data', 'Data'),
    ('aiida.orm', 'CalculationFactory', 'CalculationFactory'),
    ('aiida.orm', 'DataFactory', 'DataFactory'),
    ('aiida.orm', 'WorkflowFactory', 'WorkflowFactory'),
    ('aiida.orm.code', 'Code', 'Code'),
    ('aiida.orm.computer', 'Computer', 'Computer'),
    ('aiida.orm.group', 'Group', 'Group'),
    ('aiida.orm.workflow', 'Workflow', 'Workflow'),
    ('aiida.orm.querybuilder', 'QueryBuilder', 'QueryBuilder'),
    ('aiida.orm.utils', 'load_node', 'load_node'),
]

# -*- coding: utf-8 -*-
from __future__ import absolute_import 
import click


def validate_structure(callback_kwargs, ctx, param, value):
    """
    Command line option validator for an AiiDA structure data pk. It expects
    an integer for the value and will try to load the corresponding node. it
    will also check if successful if the node is a StructureData instance.

    :param callback_kwargs: an optional dictionary with arguments for internal use in the validator
    :param ctx: internal context of the click.command
    :param param: the click Parameter, i.e. either the Option or Argument to which the validator is hooked up
    :param value: a StructureData node pk
    :returns: a StructureData instance
    """
    from aiida.common.exceptions import NotExistent
    from aiida.orm import load_node
    from aiida.orm.data.structure import StructureData

    try:
        structure = load_node(int(value))
    except NotExistent as exception:
        raise click.BadParameter('failed to load the node<{}>\n{}'.format(value, exception))

    if not isinstance(structure, StructureData):
        raise click.BadParameter('node<{}> is not of type StructureData'.format(value))

    return structure

def validate_code(callback_kwargs, ctx, param, value):
    """
    Command line option validator for an AiiDA code. It expects a string for the value
    that corresponds to the label of an AiiDA code that has been setup.

    Accepted callback_kwargs:
        * entry_point: a calculation entry point string to define the expected calculation class.
            For example, 'quantumespresso.ph' will check that the Code that is resolved has its
            'input_plugin' attribute set to the same calculation entry point.
            If the calculation class cannot be loaded from the entry point a ValueError is thrown

    :param callback_kwargs: an optional dictionary with arguments for internal use in the validator
    :param ctx: internal context of the click.command
    :param param: the click Parameter, i.e. either the Option or Argument to which the validator is hooked up
    :param value: a Code label
    :returns: a Code instance
    """
    from aiida.common.exceptions import NotExistent, LoadingPluginFailed, MissingPluginError
    from aiida.orm import Code, CalculationFactory

    try:
        code = Code.get_from_string(value)
    except NotExistent as exception:
        raise click.BadParameter("failed to load the code with the label '{}'\n{}".format(value, exception))

    if 'entry_point' in callback_kwargs:
        entry_point = callback_kwargs['entry_point']
        try:
            cls = CalculationFactory(entry_point)
        except (LoadingPluginFailed, MissingPluginError):
            raise click.BadParameter("could not load calculation plugin for entry point '{}'".format(entry_point))

        if code.get_attr('input_plugin') != entry_point:
            raise click.BadParameter("code 'input_plugin' attribute '{}' does not match the required entry point '{}'"
                .format(code.get_attr('input_plugin'), entry_point))

    return code

def validate_pseudo_family(callback_kwargs, ctx, param, value):
    """
    Command line option validator for a pseudo potential family. The value should be a
    string that corresponds to a registered UpfData family, which is an AiiDA Group.

    :param callback_kwargs: an optional dictionary with arguments for internal use in the validator
    :param ctx: internal context of the click.command
    :param param: the click Parameter, i.e. either the Option or Argument to which the validator is hooked up
    :param value: a UpfData pseudo potential family label
    :returns: the pseudo potential family label
    """
    from aiida.common.exceptions import NotExistent
    from aiida.orm.data.upf import UpfData

    try:
        pseudo_family = UpfData.get_upf_group(value)
    except NotExistent as exception:
        raise click.BadParameter("failed to load the pseudo family the label '{}'\n{}".format(value, exception))

    return value

def validate_kpoint_mesh(callback_kwargs, ctx, param, value):
    """
    Command line option validator for a kpoints mesh tuple. The value should be a tuple
    of three positive integers out of which a KpointsData object will be created with
    a mesh equal to the tuple.

    :param callback_kwargs: an optional dictionary with arguments for internal use in the validator
    :param ctx: internal context of the click.command
    :param param: the click Parameter, i.e. either the Option or Argument to which the validator is hooked up
    :param value: a tuple of three positive integers
    :returns: a KpointsData instance
    """
    from aiida.orm.data.array.kpoints import KpointsData

    if any([type(i) != int for i in value]) or any([int(i) <= 0 for i in value]):
        raise click.BadParameter('all values of the tuple should be positive greater than zero integers')

    try:
        kpoints = KpointsData()
        kpoints.set_kpoints_mesh(value)
    except ValueError as exception:
        raise click.BadParameter("failed to create a KpointsData mesh out of {}\n{}".format(value, exception))

    return kpoints

def validate_calculation(callback_kwargs, ctx, param, value):
    """
    Command line option validator for an AiiDA JobCalculation pk. It expects
    an integer for the value and will try to load the corresponding node. it
    will also check if successful if the node is a JobCalculation instance.

    Accepted callback_kwargs:
        * entry_point: a calculation entry point string to define the expected calculation class
            For example, 'quantumespresso.ph' will check that value is instance of PhCalculation
            The default will simply check whether the value is an instance of JobCalculation.
            If the class cannot be loaded from the entry point a ValueError is thrown

    :param callback_kwargs: an optional dictionary with arguments for internal use in the validator
    :param ctx: internal context of the click.command
    :param param: the click Parameter, i.e. either the Option or Argument to which the validator is hooked up
    :param value: a JobCalculation node pk
    :returns: a JobCalculation instance
    """
    from aiida.common.exceptions import NotExistent, LoadingPluginFailed, MissingPluginError
    from aiida.orm import load_node, CalculationFactory
    from aiida.orm.calculation import JobCalculation

    if 'entry_point' in callback_kwargs:
        entry_point = callback_kwargs['entry_point']
        try:
            cls = CalculationFactory(entry_point)
        except (LoadingPluginFailed, MissingPluginError):
            raise click.BadParameter("could not load calculation plugin for entry point '{}'".format(entry_point))
    else:
        cls = JobCalculation

    try:
        calculation = load_node(int(value))
    except NotExistent as exception:
        raise click.BadParameter('failed to load the node<{}>\n{}'.format(value, exception))

    if not isinstance(calculation, cls):
        raise click.BadParameter('node<{}> is not of type {}'.format(value, cls.__name__))

    return calculation

def validate_group(callback_kwargs, ctx, param, value):
    """
    Command line option validator for an AiiDA Group. It expects a string for the value
    that corresponds to the label or a pk of an AiiDA group.

    :param callback_kwargs: an optional dictionary with arguments for internal use in the validator
    :param ctx: internal context of the click.command
    :param param: the click Parameter, i.e. either the Option or Argument to which the validator is hooked up
    :param value: a Group label or pk
    :returns: a Group instance
    """
    from aiida.common.exceptions import NotExistent
    from aiida.orm import Group

    if value is None:
        return value

    try:
        group = Group.get_from_string(value)
    except NotExistent as exception:
        pass
    else:
        return group

    try:
        group = Group.get(pk=int(value))
    except NotExistent as exception:
        raise click.BadParameter("failed to load the Group with the label or pk '{}'\n{}".format(value, exception))
    else:
        return group
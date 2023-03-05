# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-name-in-module
"""Tests to run with a running daemon."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from workchains import (
    ArithmeticAddBaseWorkChain,
    CalcFunctionRunnerWorkChain,
    DynamicDbInput,
    DynamicMixedInput,
    DynamicNonDbInput,
    ListEcho,
    NestedInputNamespace,
    NestedWorkChain,
    SerializeWorkChain,
    WorkFunctionRunnerWorkChain,
)

from aiida.common import StashMode, exceptions
from aiida.engine import run, submit
from aiida.engine.daemon.client import get_daemon_client
from aiida.engine.persistence import ObjectLoader
from aiida.engine.processes import CalcJob, Process
from aiida.manage.caching import enable_caching
from aiida.orm import CalcJobNode, Dict, Int, List, Str, load_code, load_node
from aiida.plugins import CalculationFactory, WorkflowFactory
from aiida.workflows.arithmetic.add_multiply import add, add_multiply
from tests.utils.memory import get_instances  # pylint: disable=import-error

CODENAME_ADD = 'add@localhost'
CODENAME_DOUBLER = 'doubler@localhost'
TIMEOUTSECS = 4 * 60  # 4 minutes
NUMBER_CALCULATIONS = 15  # Number of calculations to submit
NUMBER_WORKCHAINS = 8  # Number of workchains to submit


def print_daemon_log():
    """Print daemon log."""
    daemon_client = get_daemon_client()
    daemon_log = daemon_client.daemon_log_file

    print(f"Output of 'cat {daemon_log}':")
    try:
        print(subprocess.check_output(
            ['cat', f'{daemon_log}'],
            stderr=subprocess.STDOUT,
        ))
    except subprocess.CalledProcessError as exception:
        print(f'Note: the command failed, message: {exception}')


def jobs_have_finished(pks):
    """Check if jobs with given pks have finished."""
    finished_list = [load_node(pk).is_terminated for pk in pks]
    node_list = [load_node(pk) for pk in pks]
    num_finished = len([_ for _ in finished_list if _])

    for node in node_list:
        if not node.is_terminated:
            print(f'not terminated: {node.pk} [{node.process_state}]')
    print(f'{num_finished}/{len(finished_list)} finished')
    return False not in finished_list


def print_report(pk):
    """Print the process report for given pk."""
    print(f"Output of 'verdi process report {pk}':")
    try:
        print(subprocess.check_output(
            ['verdi', 'process', 'report', f'{pk}'],
            stderr=subprocess.STDOUT,
        ))
    except subprocess.CalledProcessError as exception:
        print(f'Note: the command failed, message: {exception}')


def validate_process_functions(expected_results):
    """Validate the calcfunction and workfunction."""
    valid = True
    for pk, expected_result in expected_results.items():
        calc = load_node(pk)
        if not calc.is_finished_ok:
            print(f'Calc<{pk}> not finished ok: process_state<{calc.process_state}> exit_status<{calc.exit_status}>')
            print_report(pk)
            valid = False

        try:
            actual_result = calc.outputs.result
        except exceptions.NotExistent:
            print(f'Could not retrieve `result` output for process<{pk}>')
            print_report(pk)
            valid = False

        if actual_result != expected_result:
            print(f'* UNEXPECTED VALUE {actual_result} for calc pk={pk}: I expected {expected_result}')
            valid = False

    return valid


def validate_calculations(expected_results):
    """Validate the calculations."""
    valid = True
    actual_dict = {}
    for pk, expected_dict in expected_results.items():
        calc = load_node(pk)
        if not calc.is_finished_ok:
            print(f'Calc<{pk}> not finished ok: process_state<{calc.process_state}> exit_status<{calc.exit_status}>')
            print_report(pk)
            valid = False

        try:
            actual_dict = calc.outputs.output_parameters.get_dict()
        except exceptions.NotExistent:
            print(f'Could not retrieve `output_parameters` node for Calculation<{pk}>')
            print_report(pk)
            valid = False

        try:
            actual_dict['retrieved_temporary_files'] = dict(actual_dict['retrieved_temporary_files'])
        except KeyError:
            # If the retrieval fails we simply pass as the following check of the actual value will fail anyway
            pass

        # Convert the parsed stdout content (which should be the integer followed by a newline `10\n`) to an integer
        try:
            actual_dict['value'] = int(actual_dict['value'].strip())
        except (KeyError, ValueError):
            pass

        if actual_dict != expected_dict:
            print(f'* UNEXPECTED VALUE {actual_dict} for calc pk={pk}: I expected {expected_dict}')
            valid = False

    return valid


def validate_workchains(expected_results):
    """Validate the workchains."""
    valid = True
    for pk, expected_value in expected_results.items():
        this_valid = True
        try:
            calc = load_node(pk)
            actual_value = calc.outputs.output
        except (exceptions.NotExistent, AttributeError) as exception:
            print(
                '* UNABLE TO RETRIEVE VALUE for workchain pk={}: I expected {}, I got {}: {}'.format(
                    pk, expected_value, type(exception), exception
                )
            )
            valid = False
            this_valid = False
            actual_value = None

        # I check only if this_valid, otherwise calc could not exist
        if this_valid and not calc.is_finished_ok:
            print(
                'Calculation<{}> not finished ok: process_state<{}> exit_status<{}>'.format(
                    pk, calc.process_state, calc.exit_status
                )
            )
            print_report(pk)
            valid = False
            this_valid = False

        # I check only if this_valid, otherwise actual_value could be unset
        if this_valid and actual_value != expected_value:
            print(
                '* UNEXPECTED VALUE {}, type {} for workchain pk={}: I expected {}, type {}'.format(
                    actual_value, type(actual_value), pk, expected_value, type(expected_value)
                )
            )
            valid = False
            this_valid = False

    return valid


def validate_cached(cached_calcs):
    """
    Check that the calculations with created with caching are indeed cached.
    """
    valid = True
    for calc in cached_calcs:

        if not calc.is_finished_ok:
            print(
                'Cached calculation<{}> not finished ok: process_state<{}> exit_status<{}>'.format(
                    calc.pk, calc.process_state, calc.exit_status
                )
            )
            print_report(calc.pk)
            valid = False

        if '_aiida_cached_from' not in calc.base.extras or calc.base.caching.get_hash(
        ) != calc.base.extras.get('_aiida_hash'):
            print(f'Cached calculation<{calc.pk}> has invalid hash')
            print_report(calc.pk)
            valid = False

        if isinstance(calc, CalcJobNode):
            original_calc = load_node(calc.base.extras.get('_aiida_cached_from'))
            files_original = original_calc.base.repository.list_object_names()
            files_cached = calc.base.repository.list_object_names()

            if not files_cached:
                print(f'Cached calculation <{calc.pk}> does not have any raw inputs files')
                print_report(calc.pk)
                valid = False
            if not files_original:
                print(
                    'Original calculation <{}> does not have any raw inputs files after being cached from.'.format(
                        original_calc.pk
                    )
                )
                valid = False

            if set(files_original) != set(files_cached):
                print(
                    'different raw input files [{}] vs [{}] for original<{}> and cached<{}> calculation'.format(
                        set(files_original), set(files_cached), original_calc.pk, calc.pk
                    )
                )
                valid = False

    return valid


def launch_calcfunction(inputval):
    """Launch workfunction to the daemon"""
    inputs = {
        'x': Int(inputval),
        'y': Int(inputval),
    }
    res = inputval + inputval
    expected_result = Int(res)
    process = submit(add, **inputs)
    print(f'launched calcfunction {process.uuid}, pk={process.pk}')
    return process, expected_result


def launch_workfunction(inputval):
    """Launch workfunction to the daemon"""
    inputs = {
        'x': Int(inputval),
        'y': Int(inputval),
        'z': Int(inputval),
    }
    res = (inputval + inputval) * inputval
    expected_result = Int(res)
    process = submit(add_multiply, **inputs)
    print(f'launched workfunction {process.uuid}, pk={process.pk}')
    return process, expected_result


def launch_calculation(code, counter, inputval):
    """
    Launch calculations to the daemon through the Process layer
    """
    process, inputs, expected_result = create_calculation_process(code=code, inputval=inputval)
    calc = submit(process, **inputs)
    print(f'[{counter}] launched calculation {calc.uuid}, pk={calc.pk}')
    return calc, expected_result


def run_calculation(code, counter, inputval):
    """
    Run a calculation through the Process layer.
    """
    process, inputs, expected_result = create_calculation_process(code=code, inputval=inputval)
    _, calc = run.get_node(process, **inputs)
    print(f'[{counter}] ran calculation {calc.uuid}, pk={calc.pk}')
    return calc, expected_result


def create_calculation_process(code, inputval):
    """
    Create the process and inputs for a submitting / running a calculation.
    """
    TemplatereplacerCalculation = CalculationFactory('core.templatereplacer')
    parameters = Dict(dict={'value': inputval})
    template = Dict(
        dict={
            # The following line adds a significant sleep time.
            # I set it to 1 second to speed up tests
            # I keep it to a non-zero value because I want
            # To test the case when AiiDA finds some calcs
            # in a queued state
            # 'cmdline_params': ["{}".format(counter % 3)], # Sleep time
            'cmdline_params': ['1'],
            'input_file_template': '{value}',  # File just contains the value to double
            'input_file_name': 'value_to_double.txt',
            'output_file_name': 'output.txt',
            'retrieve_temporary_files': ['triple_value.tmp']
        }
    )
    options = {
        'resources': {
            'num_machines': 1
        },
        'max_wallclock_seconds': 5 * 60,
        'withmpi': False,
        'parser_name': 'core.templatereplacer',
    }

    expected_result = {'value': 2 * inputval, 'retrieved_temporary_files': {'triple_value.tmp': str(inputval * 3)}}

    inputs = {
        'code': code,
        'parameters': parameters,
        'template': template,
        'metadata': {
            'options': options,
        }
    }
    return TemplatereplacerCalculation, inputs, expected_result


def run_arithmetic_add():
    """Run the `ArithmeticAddCalculation`."""
    ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')

    code = load_code(CODENAME_ADD)
    inputs = {
        'x': Int(1),
        'y': Int(2),
        'code': code,
    }

    # Normal inputs should run just fine
    results, node = run.get_node(ArithmeticAddCalculation, **inputs)
    assert node.is_finished_ok, node.exit_status
    assert results['sum'] == 3


def run_base_restart_workchain():
    """Run the `AddArithmeticBaseWorkChain` a few times for various inputs."""
    code = load_code(CODENAME_ADD)
    inputs = {
        'add': {
            'x': Int(1),
            'y': Int(2),
            'code': code,
        }
    }

    # Normal inputs should run just fine
    results, node = run.get_node(ArithmeticAddBaseWorkChain, **inputs)
    assert node.is_finished_ok, node.exit_status
    assert len(node.called) == 1
    assert 'sum' in results
    assert results['sum'].value == 3

    # With one input negative, the sum will be negative which will fail the calculation, but the error handler should
    # fix it, so the second calculation should finish successfully
    inputs['add']['y'] = Int(-4)
    results, node = run.get_node(ArithmeticAddBaseWorkChain, **inputs)
    assert node.is_finished_ok, node.exit_status
    assert len(node.called) == 2
    assert 'sum' in results
    assert results['sum'].value == 5

    # The silly sanity check aborts the workchain if the sum is bigger than 10
    inputs['add']['y'] = Int(10)
    results, node = run.get_node(ArithmeticAddBaseWorkChain, **inputs)
    assert not node.is_finished_ok, node.process_state
    assert node.exit_status == ArithmeticAddBaseWorkChain.exit_codes.ERROR_TOO_BIG.status, node.exit_status  # pylint: disable=no-member
    assert len(node.called) == 1

    # Check that overriding default handler enabled status works
    inputs['add']['y'] = Int(1)
    inputs['handler_overrides'] = Dict(dict={'disabled_handler': True})
    results, node = run.get_node(ArithmeticAddBaseWorkChain, **inputs)
    assert not node.is_finished_ok, node.process_state
    assert node.exit_status == ArithmeticAddBaseWorkChain.exit_codes.ERROR_ENABLED_DOOM.status, node.exit_status  # pylint: disable=no-member
    assert len(node.called) == 1


def run_multiply_add_workchain():
    """Run the `MultiplyAddWorkChain`."""
    MultiplyAddWorkChain = WorkflowFactory('core.arithmetic.multiply_add')

    code = load_code(CODENAME_ADD)
    inputs = {
        'x': Int(1),
        'y': Int(2),
        'z': Int(3),
        'code': code,
    }

    # Normal inputs should run just fine
    results, node = run.get_node(MultiplyAddWorkChain, **inputs)
    assert node.is_finished_ok, node.exit_status
    assert len(node.called) == 2
    assert 'result' in results
    assert results['result'].value == 5


def run_monitored_calculation():
    """Run a monitored calculation."""
    builder = load_code(CODENAME_ADD).get_builder()
    builder.x = Int(1)
    builder.y = Int(2)
    builder.metadata.options.sleep = 2  # Add a sleep to the calculation to ensure monitor has time to get called
    builder.monitors = {'always_kill': Dict({'entry_point': 'core.always_kill'})}

    _, node = run.get_node(builder)
    assert node.is_terminated
    assert node.exit_status == CalcJob.exit_codes.STOPPED_BY_MONITOR.status
    assert node.exit_message == 'Detected a non-empty submission script', node.exit_message


def launch_all():
    """Launch a bunch of calculation jobs and workchains.

    :returns: dictionary with expected results and pks of all launched calculations and workchains
    """
    # pylint: disable=too-many-locals,too-many-statements
    expected_results_process_functions = {}
    expected_results_calculations = {}
    expected_results_workchains = {}
    code_doubler = load_code(CODENAME_DOUBLER)

    # Run the `ArithmeticAddCalculation`
    print('Running the `ArithmeticAddCalculation`')
    run_arithmetic_add()

    # Run the `AddArithmeticBaseWorkChain`
    print('Running the `AddArithmeticBaseWorkChain`')
    run_base_restart_workchain()

    # Run the `MultiplyAddWorkChain`
    print('Running the `MultiplyAddWorkChain`')
    run_multiply_add_workchain()

    # Testing the stashing functionality
    print('Testing the stashing functionality')
    process, inputs, expected_result = create_calculation_process(code=code_doubler, inputval=1)
    with tempfile.TemporaryDirectory() as tmpdir:

        # Delete the temporary directory to test that the stashing functionality will create it if necessary
        shutil.rmtree(tmpdir, ignore_errors=True)

        source_list = ['output.txt', 'triple_value.*']
        inputs['metadata']['options']['stash'] = {'target_base': tmpdir, 'source_list': source_list}
        _, node = run.get_node(process, **inputs)
        assert node.is_finished_ok
        assert 'remote_stash' in node.outputs
        remote_stash = node.outputs.remote_stash
        assert remote_stash.stash_mode == StashMode.COPY
        assert remote_stash.target_basepath.startswith(tmpdir)
        assert sorted(remote_stash.source_list) == sorted(source_list)

        stashed_filenames = os.listdir(remote_stash.target_basepath)
        for filename in source_list:
            if '*' in filename:
                assert any(re.match(filename, stashed_file) is not None for stashed_file in stashed_filenames)
            else:
                assert filename in stashed_filenames

    # Testing the monitoring functionality
    print('Testing the monitoring functionality')
    run_monitored_calculation()

    # Submitting the calcfunction through the launchers
    print('Submitting calcfunction to the daemon')
    proc, expected_result = launch_calcfunction(inputval=1)
    expected_results_process_functions[proc.pk] = expected_result

    # Submitting the workfunction through the launchers
    print('Submitting workfunction to the daemon')
    proc, expected_result = launch_workfunction(inputval=1)
    expected_results_process_functions[proc.pk] = expected_result

    # Submitting the Calculations the new way directly through the launchers
    print(f'Submitting {NUMBER_CALCULATIONS} calculations to the daemon')
    for counter in range(1, NUMBER_CALCULATIONS + 1):
        inputval = counter
        calc, expected_result = launch_calculation(code=code_doubler, counter=counter, inputval=inputval)
        expected_results_calculations[calc.pk] = expected_result

    # Submitting the Workchains
    print(f'Submitting {NUMBER_WORKCHAINS} workchains to the daemon')
    for index in range(NUMBER_WORKCHAINS):
        inp = Int(index)
        _, node = run.get_node(NestedWorkChain, inp=inp)
        expected_results_workchains[node.pk] = index

    print("Submitting a workchain with 'submit'.")
    builder = NestedWorkChain.get_builder()
    input_val = 4
    builder.inp = Int(input_val)
    pk = submit(builder).pk
    expected_results_workchains[pk] = input_val

    print('Submitting a workchain with a nested input namespace.')
    value = Int(-12)
    pk = submit(NestedInputNamespace, foo={'bar': {'baz': value}}).pk

    print('Submitting a workchain with a dynamic non-db input.')
    value = [4, 2, 3]
    pk = submit(DynamicNonDbInput, namespace={'input': value}).pk
    expected_results_workchains[pk] = value

    print('Submitting a workchain with a dynamic db input.')
    value = 9
    pk = submit(DynamicDbInput, namespace={'input': Int(value)}).pk
    expected_results_workchains[pk] = value

    print('Submitting a workchain with a mixed (db / non-db) dynamic input.')
    value_non_db = 3
    value_db = Int(2)
    pk = submit(DynamicMixedInput, namespace={'inputs': {'input_non_db': value_non_db, 'input_db': value_db}}).pk
    expected_results_workchains[pk] = value_non_db + value_db

    print('Submitting the serializing workchain')
    pk = submit(SerializeWorkChain, test=Int).pk
    expected_results_workchains[pk] = ObjectLoader().identify_object(Int)

    print('Submitting the ListEcho workchain.')
    list_value = List()
    list_value.extend([1, 2, 3])
    pk = submit(ListEcho, list=list_value).pk
    expected_results_workchains[pk] = list_value

    print('Submitting a WorkChain which contains a workfunction.')
    value = Str('workfunction test string')
    pk = submit(WorkFunctionRunnerWorkChain, input=value).pk
    expected_results_workchains[pk] = value

    print('Submitting a WorkChain which contains a calcfunction.')
    value = Int(1)
    pk = submit(CalcFunctionRunnerWorkChain, input=value).pk
    expected_results_workchains[pk] = Int(2)

    calculation_pks = sorted(expected_results_calculations.keys())
    workchains_pks = sorted(expected_results_workchains.keys())
    process_functions_pks = sorted(expected_results_process_functions.keys())

    return {
        'pks': calculation_pks + workchains_pks + process_functions_pks,
        'calculations': expected_results_calculations,
        'process_functions': expected_results_process_functions,
        'workchains': expected_results_workchains,
    }


def relaunch_cached(results):
    """Launch the same calculations but with caching enabled -- these should be FINISHED immediately."""
    code_doubler = load_code(CODENAME_DOUBLER)
    cached_calcs = []
    with enable_caching(identifier='aiida.calculations:core.templatereplacer'):
        for counter in range(1, NUMBER_CALCULATIONS + 1):
            inputval = counter
            calc, expected_result = run_calculation(code=code_doubler, counter=counter, inputval=inputval)
            cached_calcs.append(calc)
            results['calculations'][calc.pk] = expected_result

    if not (
        validate_calculations(results['calculations']) and validate_workchains(results['workchains']) and
        validate_cached(cached_calcs) and validate_process_functions(results['process_functions'])
    ):
        print_daemon_log()
        print('')
        print('ERROR! Some return values are different from the expected value')
        sys.exit(3)

    print_daemon_log()
    print('')
    print('OK, all calculations have the expected parsed result')


def main():
    """Launch a bunch of calculation jobs and workchains."""

    results = launch_all()

    print('Waiting for end of execution...')
    start_time = time.time()
    exited_with_timeout = True
    while time.time() - start_time < TIMEOUTSECS:
        time.sleep(15)  # Wait a few seconds

        # Print some debug info, both for debugging reasons and to avoid
        # that the test machine is shut down because there is no output

        print('#' * 78)
        print(f'####### TIME ELAPSED: {time.time() - start_time} s')
        print('#' * 78)
        print("Output of 'verdi process list -a':")
        try:
            print(subprocess.check_output(
                ['verdi', 'process', 'list', '-a'],
                stderr=subprocess.STDOUT,
            ))
        except subprocess.CalledProcessError as exception:
            print(f'Note: the command failed, message: {exception}')

        print("Output of 'verdi daemon status':")
        try:
            print(subprocess.check_output(
                ['verdi', 'daemon', 'status'],
                stderr=subprocess.STDOUT,
            ))
        except subprocess.CalledProcessError as exception:
            print(f'Note: the command failed, message: {exception}')

        if jobs_have_finished(results['pks']):
            print('Calculation terminated its execution')
            exited_with_timeout = False
            break

    if exited_with_timeout:
        print_daemon_log()
        print('')
        print(f'Timeout!! Calculation did not complete after {TIMEOUTSECS} seconds')
        sys.exit(2)

    relaunch_cached(results)

    # Check that no references to processes remain in memory
    # Note: This tests only processes that were `run` in the same interpreter, not those that were `submitted`
    del results
    processes = get_instances(Process, delay=1.0)
    if processes:
        print(f'Memory leak! Process instances remained in memory: {processes}')
        sys.exit(4)

    sys.exit(0)


if __name__ == '__main__':
    main()

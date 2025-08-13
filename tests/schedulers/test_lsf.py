###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `LsfScheduler` plugin."""

import logging
import uuid

import pytest

from aiida.common.exceptions import ConfigurationError
from aiida.schedulers.datastructures import JobState
from aiida.schedulers.plugins.lsf import LsfScheduler
from aiida.schedulers.scheduler import SchedulerError

BJOBS_STDOUT_TO_TEST = (
    '764213236|EXIT|TERM_RUNLIMIT: job killed after reaching LSF run time limit'
    '|b681e480bd|inewton|1|-|b681e480bd|test|Feb  2 00:46|Feb  2 00:45|-|Feb  2 00:44'
    '|aiida-1033269\n'
    '764220165|PEND|-|-|inewton|-|-|-|8nm|-|-|-|Feb  2 01:46|aiida-1033444\n'
    '764220167|PEND|-|-|fchopin|-|-|-|test|-|-|-|Feb  2 01:53 L|aiida-1033449\n'
    '764254593|RUN|-|lxbsu2710|inewton|1|-|lxbsu2710|test|Feb  2 07:40|Feb  2 07:39|-|Feb  2 07:39|'
    'test\n764255172|RUN|-|b68ac74822|inewton|1|-|b68ac74822|test|Feb  2 07:48 L|Feb  2 07:47| '
    '15.00% L|Feb  2 07:47|test\n764245175|RUN|-|b68ac74822|dbowie|1|-|b68ac74822|test|'
    'Jan  1 05:07|Dec  31 23:48 L|25.00%|Dec  31 23:40|test\n 764399747|DONE|-|p05496706j68144|'
    'inewton|1|-|p05496706j68144|test|Feb  2 14:56 L|Feb  2 14:54|38.33% L|Feb  2 14:54|test'
)
BJOBS_STDERR_TO_TEST = 'Job <864220165> is not found'

SUBMIT_STDOUT_TO_TEST = 'Job <764254593> is submitted to queue <test>.'
BKILL_STDOUT_TO_TEST = 'Job <764254593> is being terminated'


def test_parse_common_joblist_output():
    """Tests to verify if the function _parse_joblist_output can parse the bjobs output.
    The tests is done parsing a string defined above, to be used offline
    """
    import datetime

    scheduler = LsfScheduler()

    # Disable logging to avoid excessive output during test
    logging.disable(logging.ERROR)

    retval = 255
    stdout = BJOBS_STDOUT_TO_TEST
    stderr = BJOBS_STDERR_TO_TEST

    with pytest.raises(SchedulerError):
        job_list = scheduler._parse_joblist_output(retval, stdout, stderr)

    retval = 0
    stdout = BJOBS_STDOUT_TO_TEST
    stderr = ''
    job_list = scheduler._parse_joblist_output(retval, stdout, stderr)

    # The parameters are hard coded in the text to parse
    job_on_cluster = 7
    job_parsed = len(job_list)
    assert job_parsed == job_on_cluster

    job_queued = 2
    job_queue_name = ['8nm', 'test']
    job_queued_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED])
    job_queue_name_parsed = [j.queue_name for j in job_list if j.job_state and j.job_state == JobState.QUEUED]
    assert job_queued == job_queued_parsed
    assert job_queue_name == job_queue_name_parsed

    job_done = 2
    job_done_title = ['aiida-1033269', 'test']
    job_done_annotation = ['TERM_RUNLIMIT: job killed after reaching LSF run time limit', '-']
    job_done_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.DONE])
    job_done_title_parsed = [j.title for j in job_list if j.job_state and j.job_state == JobState.DONE]
    job_done_annotation_parsed = [j.annotation for j in job_list if j.job_state and j.job_state == JobState.DONE]
    assert job_done == job_done_parsed
    assert job_done_title == job_done_title_parsed
    assert job_done_annotation == job_done_annotation_parsed

    job_running = 3
    job_running_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.RUNNING])
    assert job_running == job_running_parsed

    running_users = ['inewton', 'inewton', 'dbowie']
    parsed_running_users = [j.job_owner for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
    assert running_users == parsed_running_users

    running_jobs = ['764254593', '764255172', '764245175']
    num_machines = [1, 1, 1]
    allocated_machines = ['lxbsu2710', 'b68ac74822', 'b68ac74822']
    parsed_running_jobs = [j.job_id for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
    parsed_num_machines = [j.num_machines for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
    parsed_allocated_machines = [
        j.allocated_machines_raw for j in job_list if j.job_state and j.job_state == JobState.RUNNING
    ]
    assert running_jobs == parsed_running_jobs
    assert num_machines == parsed_num_machines
    assert allocated_machines == parsed_allocated_machines

    assert next(j.requested_wallclock_time_seconds for j in job_list if j.job_id == '764254593') == 60
    assert next(j.wallclock_time_seconds for j in job_list if j.job_id == '764255172') == 9
    assert next(j.wallclock_time_seconds for j in job_list if j.job_id == '764245175') == 4785
    current_year = datetime.datetime.now().year
    assert next(j.submission_time for j in job_list if j.job_id == '764245175') == datetime.datetime(
        current_year, 12, 31, 23, 40
    )

    # Important to enable again logs!
    logging.disable(logging.NOTSET)


def test_submit_script():
    """Test the creation of a simple submission script"""
    from aiida.common.datastructures import CodeRunMode
    from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

    scheduler = LsfScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.shebang = '#!/bin/bash'
    job_tmpl.uuid = str(uuid.uuid4())
    job_tmpl.job_resource = scheduler.create_job_resource(tot_num_mpiprocs=2, parallel_env='b681e480bd.cern.ch')
    job_tmpl.max_wallclock_seconds = 24 * 3600
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = ['mpirun', '-np', '2', 'pw.x', '-npool', '1']
    tmpl_code_info.stdin_name = 'aiida.in'
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL
    job_tmpl.account = 'account_id'

    submit_script_text = scheduler.get_submit_script(job_tmpl)

    assert submit_script_text.startswith('#!/bin/bash')

    assert '#BSUB -rn' in submit_script_text
    assert '#BSUB -n 2' in submit_script_text
    assert '#BSUB -W 24:00' in submit_script_text
    assert '#BSUB -G account_id' in submit_script_text
    assert "'mpirun' '-np' '2' 'pw.x' '-npool' '1' < 'aiida.in'" in submit_script_text


def test_submit_script_rerunnable():
    """Test the `rerunnable` option of the submit script."""
    from aiida.common.datastructures import CodeRunMode
    from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

    scheduler = LsfScheduler()

    job_tmpl = JobTemplate()
    job_tmpl.job_resource = scheduler.create_job_resource(tot_num_mpiprocs=2, parallel_env='b681e480bd.cern.ch')
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = []
    job_tmpl.codes_info = [tmpl_code_info]
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    job_tmpl.rerunnable = True
    submit_script_text = scheduler.get_submit_script(job_tmpl)
    assert '#BSUB -r\n' in submit_script_text
    assert '#BSUB -rn' not in submit_script_text

    job_tmpl.rerunnable = False
    submit_script_text = scheduler.get_submit_script(job_tmpl)
    assert '#BSUB -r\n' not in submit_script_text
    assert '#BSUB -rn' in submit_script_text


@pytest.mark.parametrize(
    'kwargs, exception, message',
    (
        (
            {'tot_num_mpiprocs': 'Not-a-Number'},
            TypeError,
            '`tot_num_mpiprocs` must be specified and must be an integer',
        ),
        ({'parallel_env': 0}, TypeError, 'parallel_env` must be a string'),
        ({'num_machines': 1}, ConfigurationError, '`num_machines` cannot be set unless `use_num_machines` is `True`.'),
        ({'use_num_machines': True}, ConfigurationError, 'must set `num_machines` when `use_num_machines` is `True`.'),
        ({'num_machines': 'string', 'use_num_machines': True}, TypeError, '`num_machines` must be an integer'),
        ({}, TypeError, '`tot_num_mpiprocs` must be specified and must be an integer'),
        ({'tot_num_mpiprocs': 'string'}, TypeError, '`tot_num_mpiprocs` must be specified and must be an integer'),
        ({'tot_num_mpiprocs': 0}, ValueError, 'tot_num_mpiprocs must be >= 1'),
        ({'default_mpiprocs_per_machine': 1}, ConfigurationError, '`default_mpiprocs_per_machine` cannot be set.'),
    ),
)
def test_create_job_resource(kwargs, exception, message):
    """Test to verify that script fails in the following cases:
    * if we specify only num_machines
    * if tot_num_mpiprocs is not an int (and can't be casted to one)
    * if parallel_env is not a str
    """
    scheduler = LsfScheduler()

    with pytest.raises(exception, match=message):
        scheduler.create_job_resource(**kwargs)


def test_submit_output():
    """Test the parsing of the submit response"""
    scheduler = LsfScheduler()
    retval = 0
    stdout = SUBMIT_STDOUT_TO_TEST
    stderr = ''

    assert scheduler._parse_submit_output(retval, stdout, stderr) == '764254593'


def test_kill_output():
    """Test the parsing of the kill response"""
    scheduler = LsfScheduler()
    retval = 0
    stdout = BKILL_STDOUT_TO_TEST
    stderr = ''

    assert scheduler._parse_kill_output(retval, stdout, stderr)


def test_job_tmpl_errors():
    """Test the raising of the appropriate errors"""
    from aiida.common.datastructures import CodeRunMode
    from aiida.schedulers.datastructures import JobTemplate

    scheduler = LsfScheduler()
    job_tmpl = JobTemplate()

    # Raises for missing resources with tot_num_mpiprocs
    with pytest.raises(ValueError):
        scheduler.get_submit_script(job_tmpl)
    job_tmpl.job_resource = scheduler.create_job_resource(tot_num_mpiprocs=2)
    job_tmpl.codes_info = []

    # Raises for missing codes_run_mode
    with pytest.raises(NotImplementedError):
        scheduler.get_submit_script(job_tmpl)
    job_tmpl.codes_run_mode = CodeRunMode.SERIAL

    # Incorrect setups
    job_tmpl.max_wallclock_seconds = 'Not-a-Number'
    with pytest.raises(ValueError):
        scheduler.get_submit_script(job_tmpl)
    job_tmpl.pop('max_wallclock_seconds')

    job_tmpl.max_memory_kb = 'Not-a-Number'
    with pytest.raises(ValueError):
        scheduler.get_submit_script(job_tmpl)
    job_tmpl.pop('max_memory_kb')

    # Verify minimal working parameters don't raise
    scheduler.get_submit_script(job_tmpl)


def test_parsing_errors():
    """Test the raising of the appropriate errors"""
    from aiida.schedulers import SchedulerParsingError

    scheduler = LsfScheduler()

    with pytest.raises(SchedulerParsingError) as exc:
        scheduler._parse_submit_output(0, 'Bad-Output-String', '')
    assert '`Bad-Output-String`' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        scheduler._parse_time_string('Bad-Time-String')
    assert '`Bad-Time-String`' in str(exc.value)

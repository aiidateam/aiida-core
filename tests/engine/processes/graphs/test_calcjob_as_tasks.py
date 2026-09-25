###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The steps of a calculation job, written as tasks of a graph.

A ``CalcJob`` runs upload, submit, poll and parse inside one process, so none of them can be retried, inspected
or recomposed on its own, and the parser arrives as an input because there is no step for it to be the class
of. Here each step is a task, so each is a process with its own node, and the parser is the task that parses.

Eight of the nine operations a calculation job performs are here: unstash, upload, submit, poll, stash,
kill, retrieve and parse. The ninth is what a calcjob monitor does beyond watching. ``@monitor`` answers yes
or no, so a monitor that has seen enough can call ``kill_job`` itself, and it still cannot say what
``CalcJobMonitorAction`` says: stop without retrieving, or parse but override the exit code. That is a word
the graph layer does not have, rather than a step that is missing.

``upload`` also puts the sandbox on the computer and nothing else, where ``execmanager.upload_calculation``
handles the copy lists, stashing and provenance exclusion, and takes a ``CalcJobNode`` to do it. Extracting
that the way ``CalcJob.describe`` was extracted is what these steps need before they can replace the engine's
own path.

Marked ``nightly``: each test runs a job end to end over a transport, and in a full run of this package they
also make the first daemon test wait out its timeout, which is unexplained and tracked in the design notes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.datastructures import JobState, StashMode
from aiida.common.folders import SandboxFolder
from aiida.engine import graph, monitor, run_get_node, task, task_node
from aiida.engine.processes.greenback import sync_await


def _options(stash_to: Path | None = None) -> dict:
    options: dict = {'resources': {'num_machines': 1}}

    if stash_to is not None:
        options['stash'] = {
            'stash_mode': StashMode.COPY.value,
            'source_list': ['aiida.out'],
            'target_base': str(stash_to),
        }

    return options


@task(outputs=['remote_folder', 'job'])
def upload(code: orm.AbstractCode, x: orm.Int, y: orm.Int, stash_to: str = '') -> tuple[orm.RemoteData, dict]:
    """Write what the calculation takes, and put it where it runs."""
    computer = code.computer
    # The node is the identity: the engine resumes this task against the same one, so the directory it names
    # is the same directory, and running the task afresh gives a new node and so a new directory.
    identity = task_node().uuid.replace('-', '')
    options = _options(Path(stash_to) if stash_to else None)
    inputs = {'code': code, 'x': x, 'y': y, 'metadata': {'options': options}}

    with SandboxFolder() as folder:
        described = ArithmeticAddCalculation.describe(
            inputs, folder, computer=computer, uuid=identity, label=f'aiida-{identity[:8]}'
        )

        with computer.get_transport() as transport:
            home = sync_await(transport.whoami_async())
            workdir = Path(computer.get_workdir().format(username=home)) / identity[:2] / identity[2:]
            sync_await(transport.makedirs_async(str(workdir), ignore_existing=True))

            for name in folder.get_content_list():
                sync_await(transport.put_async(folder.get_abs_path(name), str(workdir / name)))

    job = {
        'script': described.options['submit_script_filename'],
        'retrieve': described.retrieve_list,
        'workdir': str(workdir),
        'computer': computer.pk,
        'stash': options.get('stash', {}),
    }

    return orm.RemoteData(remote_path=str(workdir), computer=computer), job


@task(outputs=['job'])
def submit(remote_folder: orm.RemoteData, job: dict) -> dict:
    """Hand the job to the scheduler of the computer it was put on."""
    node = task_node()
    submitted = node.record.get('job_id')

    # Written before this returns, so a worker that dies here finds the job instead of submitting a second
    # one, which is what `submit_calculation` does with the job's own node.
    if submitted is not None:
        return {'job': {**job, 'id': submitted}}

    computer = remote_folder.computer
    scheduler = computer.get_scheduler()

    with computer.get_transport() as transport:
        scheduler.set_transport(transport)
        job_id = scheduler.submit_job(job['workdir'], job['script'])

    node.set_record(job_id=job_id)

    return {'job': {**job, 'id': job_id}}


@monitor
def finished(job: dict) -> bool:
    """Say whether the scheduler is done with the job, which is what waiting for one amounts to."""
    computer = orm.load_computer(pk=job['computer'])
    scheduler = computer.get_scheduler()

    with computer.get_transport() as transport:
        scheduler.set_transport(transport)
        info = scheduler.get_jobs([job['id']], as_dict=True).get(job['id'])

    # A scheduler that keeps a finished job in its listing says so by its state, and one that forgets it
    # answers with nothing at all, so both are what being done looks like.
    return info is None or info.job_state is JobState.DONE


@task(outputs=['stashed'])
def stash(remote_folder: orm.RemoteData, job: dict) -> orm.RemoteStashFolderData:
    """Keep what is worth keeping, where the scratch directory going away will not take it.

    The engine runs this only when the `stash` option asks for it, which a graph says with `branch`.
    """
    wanted = job['stash']
    identity = task_node().uuid.replace('-', '')
    target = Path(wanted['target_base']) / identity[:2] / identity[2:]

    with remote_folder.computer.get_transport() as transport:
        sync_await(transport.makedirs_async(str(target), ignore_existing=True))

        for name in wanted['source_list']:
            sync_await(transport.copy_async(str(Path(job['workdir']) / name), str(target / name)))

    return orm.RemoteStashFolderData(
        computer=remote_folder.computer,
        stash_mode=StashMode(wanted['stash_mode']),
        target_basepath=str(target),
        source_list=wanted['source_list'],
    )


@task(outputs=['restored'])
def unstash(stashed: orm.RemoteStashFolderData, into: str) -> orm.RemoteData:
    """Put back what was kept, which is how a later run starts from it."""
    computer = stashed.computer
    target = Path(into)

    with computer.get_transport() as transport:
        sync_await(transport.makedirs_async(str(target), ignore_existing=True))

        for name in stashed.source_list:
            sync_await(transport.copy_async(str(Path(stashed.target_basepath) / name), str(target / name)))

    return orm.RemoteData(remote_path=str(target), computer=computer)


@task(outputs=['killed'])
def kill_job(job: dict) -> bool:
    """Stop the job on the scheduler, which is what a monitor asks for when it has seen enough.

    A step can do this because it holds the job id, and it holds the job id because `submit` wrote it on its
    own node. What it cannot do is tell the graph what to do next, which is what `CalcJobMonitorAction` says
    and the graph layer has no word for.
    """
    computer = orm.load_computer(pk=job['computer'])
    scheduler = computer.get_scheduler()

    with computer.get_transport() as transport:
        scheduler.set_transport(transport)

        return bool(scheduler.kill_job(job['id']))


@task(outputs=['retrieved'])
def collect(remote_folder: orm.RemoteData, job: dict) -> orm.FolderData:
    """Bring back the files the calculation was told to keep."""
    retrieved = orm.FolderData()

    with remote_folder.computer.get_transport() as transport:
        with SandboxFolder() as folder:
            for name in job['retrieve']:
                sync_await(transport.get_async(str(Path(job['workdir']) / name), folder.get_abs_path(name)))

            retrieved.base.repository.put_object_from_tree(folder.abspath)

    return retrieved


@task(outputs=['sum'])
def parse(retrieved: orm.FolderData) -> orm.Int:
    """Read what came back. This task is the parser: nothing was passed one."""
    with retrieved.base.repository.open('aiida.out') as handle:
        return orm.Int(int(handle.read().strip()))


@graph
def add_on_a_computer(code, x, y, stash_to=''):
    """The steps of a calculation job, each a process of its own."""
    uploaded = upload(code=code, x=x, y=y, stash_to=stash_to)
    submitted = submit(remote_folder=uploaded.remote_folder, job=uploaded.job)
    waited = finished(job=submitted.job, interval=1.0)
    stashed = stash(remote_folder=uploaded.remote_folder, job=submitted.job).after(waited)
    collected = collect(remote_folder=uploaded.remote_folder, job=submitted.job).after(waited)

    return {'sum': parse(retrieved=collected.retrieved).sum, 'stashed': stashed.stashed}


@pytest.mark.nightly
@pytest.mark.requires_rmq
def test_a_calculation_job_runs_as_tasks(aiida_code_installed, tmp_path):
    """Every step is a process, the graph holds them together, and the parser is the task that parses."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    results, node = run_get_node(add_on_a_computer, code=code, x=orm.Int(2), y=orm.Int(3), stash_to=str(tmp_path))

    assert node.is_finished_ok, node.exit_message
    assert results['sum'].value == 5


@pytest.mark.nightly
@pytest.mark.requires_rmq
def test_each_step_is_a_process_of_its_own(aiida_code_installed, tmp_path):
    """The point of the decomposition: four nodes where a calculation job leaves one."""
    from aiida.engine import tasks

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    _, node = run_get_node(add_on_a_computer, code=code, x=orm.Int(2), y=orm.Int(3), stash_to=str(tmp_path))

    assert sorted(tasks(node)) == ['collect', 'finished', 'parse', 'stash', 'submit', 'upload']


@pytest.mark.nightly
@pytest.mark.requires_rmq
def test_each_step_is_addressable_by_its_own_node(aiida_code_installed, tmp_path):
    """A step records against its node, which is what lets it be run again without repeating itself."""
    from aiida.engine import tasks

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    _, node = run_get_node(add_on_a_computer, code=code, x=orm.Int(2), y=orm.Int(3), stash_to=str(tmp_path))
    ran = tasks(node)

    identity = ran['upload'].uuid.replace('-', '')
    uploaded = ran['upload'].outputs.remote_folder

    assert uploaded.get_remote_path().endswith(f'{identity[:2]}/{identity[2:]}'), 'named after the node'
    assert ran['submit'].record['job_id'] == ran['submit'].outputs.job['id'], 'the id is on the node'


@pytest.mark.nightly
@pytest.mark.requires_rmq
def test_what_is_stashed_survives_the_working_directory(aiida_code_installed, tmp_path):
    """Stashing keeps a file where the scratch directory going away will not take it, and unstash puts it back."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    results, node = run_get_node(add_on_a_computer, code=code, x=orm.Int(2), y=orm.Int(3), stash_to=str(tmp_path))
    stashed = results['stashed']

    assert node.is_finished_ok, node.exit_message
    assert (Path(stashed.target_basepath) / 'aiida.out').read_text().strip() == '5'

    restored, run = run_get_node(unstash, stashed=stashed, into=str(tmp_path / 'again'))

    assert run.is_finished_ok, run.exit_message
    assert (Path(restored['restored'].get_remote_path()) / 'aiida.out').read_text().strip() == '5'


@pytest.mark.nightly
@pytest.mark.requires_rmq
def test_a_running_job_can_be_stopped(aiida_localhost, tmp_path):
    """Killing is an operation a step can carry out, since the job id is on the node that submitted it."""
    script = tmp_path / 'sleeper.sh'
    script.write_text('#!/bin/bash\nsleep 120\n')

    scheduler = aiida_localhost.get_scheduler()

    with aiida_localhost.get_transport() as transport:
        scheduler.set_transport(transport)
        job_id = scheduler.submit_job(str(tmp_path), script.name)

    job = {'id': job_id, 'computer': aiida_localhost.pk}
    results, node = run_get_node(kill_job, job=job)

    assert node.is_finished_ok, node.exit_message
    assert results['killed'].value is True

    with aiida_localhost.get_transport() as transport:
        scheduler.set_transport(transport)
        info = scheduler.get_jobs([job_id], as_dict=True).get(job_id)

    assert info is None or info.job_state is JobState.DONE, 'the job is no longer running'

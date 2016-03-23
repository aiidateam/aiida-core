# -*- coding: utf-8 -*-

from aiida.workflows2.process import Process

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class SubmitInputs(Process):
    @staticmethod
    def _init(spec):
        from aiida.orm.code import Code
        spec.add_input('code', type=Code)

    def _run(self):
        pass


def tosubmit_to_withscheduler(calc, trans_pool, logger):
    """
    Submit a calculation

    :param aiida.orm.JobCalculation calc: the calculation to submit.
    :param trans_pool: the transport pool to use for opening new transports.
    :param logger: the logger to log messages to.
    :return:
    """
    from aiida.orm import Code, Computer
    from aiida.common.folders import SandboxFolder
    from aiida.common.exceptions import InputValidationError
    from aiida.orm.data.remote import RemoteData
    from aiida.djsite.utils import get_dblogger_extra

    authinfo = util.get_authinfo(calc)
    if not authinfo.enabled:
        return False

    if calc._has_cached_links():
        raise ValueError("Cannot submit calculation {} because it has "
                         "cached input links! If you "
                         "just want to test the submission, use the "
                         "test_submit() method, otherwise store all links"
                         "first".format(calc.pk))

    if calc.get_state() != calc_states.TOSUBMIT:
        raise StateError.invalid_transition(calc.get_state(),
                                            calc_states.WITHSCHEDULER)

    logger_extra = get_dblogger_extra(calc)
    with trans_pool.open_transport(authinfo) as transport:
        transport._set_logger_extra(logger_extra)

        s = Computer(dbcomputer=authinfo.dbcomputer).get_scheduler()
        s.set_transport(transport)

        computer = calc.get_computer()

        with SandboxFolder() as folder:
            calcinfo, script_filename = calc._presubmit(
                folder, use_unstored_links=False)

            codes_info = calcinfo.codes_info
            input_codes = [Code.get_subclass_from_uuid(_.code_uuid) for _ in codes_info]

            for code in input_codes:
                if not code.can_run_on(computer):
                    raise InputValidationError(
                        "The selected code {} for calculation "
                        "{} cannot run on computer {}".format(
                            code.pk, calc.pk, computer.name))

            # After this call, no modifications to the folder should be done
            calc._store_raw_input_folder(folder.abspath)

            # NOTE: some logic is partially replicated in the 'test_submit'
            # method of JobCalculation. If major logic changes are done
            # here, make sure to update also the test_submit routine
            # TODO Doc: {username} field
            # TODO: if something is changed here, fix also 'verdi computer test'
            remote_workdir = authinfo.get_workdir().format(
                username=transport.whoami())
            if not remote_workdir.strip():
                raise ConfigurationError(
                    "[submission of calc {}] "
                    "No remote_working_directory configured for computer "
                    "'{}'".format(calc.pk, computer.name))

            # If it already exists, no exception is raised
            try:
                _create_remote_workdir(remote_workdir, transport)
            except (IOError, OSError) as e:
                raise ConfigurationError(
                    "[submission of calc {}] "
                    "Unable to create the remote directory {} on "
                    "computer '{}': {}".format(
                        calc.pk, remote_workdir, computer.name,
                        e.message))

            calcdir = _create_remote_calc_dir(calcinfo, transport)
            # I store the workdir of the calculation for later file retrieval
            calc._set_remote_workdir(calcdir)

            # I first create the code files, so that the code can put
            # default files to be overwritten by the plugin itself.
            # Still, beware! The code file itself could be overwritten...
            # But I checked for this earlier.
            for code in input_codes:
                if code.is_local():
                    # Note: this will possibly overwrite files
                    for f in code.get_folder_list():
                        transport.put(code.get_abs_path(f), f)
                    transport.chmod(code.get_local_executable(), 0755)  # rwxr-xr-x

            # copy all files, recursively with folders
            for f in folder.get_content_list():
                logger.debug(
                    "[submission of calc {}] "
                    "copying file/folder {}...".format(calc.pk, f),
                    extra=logger_extra)
                transport.put(folder.get_abs_path(f), f)

        # Prepare the submission files on the remote host
        _prepare_remote_files(calcinfo, calc, transport, logger, logger_extra)

        remotedata = RemoteData(computer=computer, remote_path=calcdir)
        remotedata._add_link_from(calc, label='remote_folder')
        remotedata.store()

        job_id = s.submit_from_script(calcdir, script_filename)
        calc._set_job_id(job_id)

        ## I do not set the state to queued; in this way, if the
        ## daemon is down, the user sees '(unknown)' as last state
        ## and understands that the daemon is not running.
        # if job_tmpl.submit_as_hold:
        #    calc._set_scheduler_state(job_states.QUEUED_HELD)
        # else:
        #    calc._set_scheduler_state(job_states.QUEUED)

        logger.debug("submitted calculation {} on {} with jobid {}".
                     format(calc.pk, computer.name, job_id),
                     extra=logger_extra)
    return True


def _prepare_remote_files(calcinfo, calc, transport, logger, logger_extra):
    """
    Copy over the files necessary to carry out a calculation on a remote
    resource.

    :param calcinfo: the calculation info.
    :param calc: the calculation itself.
    :param transport: the transport to the remote computer.
    :param logger: the logger to log message to.
    :param logger_extra: logger extras to attach to messages.
    """
    computer = calc.get_computer()

    # local_copy_list is a list of tuples,
    # each with (src_abs_path, dest_rel_path)
    # NOTE: validation of these lists are done inside calc._presubmit()
    if calcinfo.local_copy_list is not None:
        for src_abs_path, dest_rel_path in calcinfo.local_copy_list:
            logger.debug(
                "[submission of calc {}] copying local file/folder to {}". \
                    format(calc.pk, dest_rel_path),
                extra=logger_extra)
            transport.put(src_abs_path, dest_rel_path)

    if calcinfo.remote_copy_list is not None:
        for (remote_computer_uuid, remote_abs_path, dest_rel_path) in \
                calcinfo.remote_copy_list:
            if remote_computer_uuid == computer.uuid:
                logger.debug("[submission of calc {}] "
                             "copying {} remotely, directly on the machine "
                             "{}".format(calc.pk, dest_rel_path, computer.name))
                try:
                    transport.copy(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    logger.warning("[submission of calc {}] "
                                   "Unable to copy remote resource from {} to {}! "
                                   "Stopping.".format(calc.pk,
                                                      remote_abs_path, dest_rel_path),
                                   extra=logger_extra)
                    raise
            else:
                # TODO: implement copy between two different machines!
                raise NotImplementedError(
                    "[presubmission of calc {}] "
                    "Remote copy between two different machines is "
                    "not implemented yet".format(calc.pk))

    if calcinfo.remote_symlink_list is not None:
        for (remote_computer_uuid, remote_abs_path, dest_rel_path) in \
                calcinfo.remote_symlink_list:
            if remote_computer_uuid == computer.uuid:
                logger.debug("[submission of calc {}] "
                             "copying {} remotely, directly on the machine "
                             "{}".format(calc.pk, dest_rel_path, computer.name))
                try:
                    transport.symlink(remote_abs_path, dest_rel_path)
                except (IOError, OSError):
                    logger.warning("[submission of calc {}] "
                                   "Unable to create remote symlink from {} to {}! "
                                   "Stopping.".format(calc.pk,
                                                      remote_abs_path, dest_rel_path),
                                   extra=logger_extra)
                    raise
            else:
                raise IOError("It is not possible to create a symlink "
                              "between two different machines for "
                              "calculation {}".format(calc.pk))


def _create_remote_workdir(workdir, transport):
    """
    Create the remote working directory for AiiDA and cd to it.

    :param workdir: the directory name.
    :param calc: the calculation currently being submitted.
    :param transport: the transport to the remote computer.
    :param logger: the logger to log message to.
    :param logger_extra: logger extras to attach to messages.
    """
    try:
        transport.chdir(workdir)
    except IOError:
        transport.makedirs(workdir)
        transport.chdir(workdir)


def _create_remote_calc_dir(calcinfo, transport):
    """
    Create  the remote working directory for a particular calculation and cd
    to it.

    :param calcinfo: information about the calculation.
    :param transport: the transport to the remote computer
    :return: The working directory
    """
    # Store remotely with sharding (here is where we choose
    # the folder structure of remote jobs; then I store this
    # in the calculation properties using _set_remote_dir
    # and I do not have to know the logic, but I just need to
    # read the absolute path from the calculation properties.
    transport.mkdir(calcinfo.uuid[:2], ignore_existing=True)
    transport.chdir(calcinfo.uuid[:2])
    transport.mkdir(calcinfo.uuid[2:4], ignore_existing=True)
    transport.chdir(calcinfo.uuid[2:4])
    transport.mkdir(calcinfo.uuid[4:])
    transport.chdir(calcinfo.uuid[4:])
    return transport.getcwd()

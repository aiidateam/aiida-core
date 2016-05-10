# -*- coding: utf-8 -*-

import plum.port as port
from abc import ABCMeta
from aiida.common.datastructures import calc_states
from aiida.scheduler.datastructures import job_states
from aiida.common.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ModificationNotAllowed,
)
from aiida.common.links import LinkType
from aiida.workflows2.process import Process
import time

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class JobCalculation(Process):
    __metaclass__ = ABCMeta

    CALC_NODE_LABEL = 'calc_node'

    @classmethod
    def build(cls, calc_class):

        def _define(spec):
            for k, v in calc_class._use_methods.iteritems():
                if v.get('additional_parameter'):
                    spec.input_group(v['linkname'], help=v.get('docstring', None),
                                     valid_type=v['valid_types'], required=False)
                else:
                    spec.input(v['linkname'], help=v.get('docstring', None),
                               valid_type=v['valid_types'], required=False)
            spec.has_dynamic_output()

        return type(calc_class.__name__, (JobCalculation,),
                    {'_define': staticmethod(_define),
                     '_CALC_CLASS': calc_class})

    def __init__(self):
        super(JobCalculation, self).__init__()

        self._poll_interval = 30
        self._computer = None
        self._resources = None
        self._custom_scheduler_commands = None
        self._queue_name = None
        self._resources = None
        self._max_wallclock_seconds = None

    def set_computer(self, computer):
        self._computer = computer

    def set_resources(self, resources):
        self._resources = resources

    def set_custom_scheduler_commands(self, commands):
        self._custom_scheduler_commands = commands

    def set_queue_name(self, queue_name):
        self._queue_name

    def set_resources(self, resources):
        self._resources = resources

    def set_max_wallclock_seconds(self, time):
        self._max_wallclock_seconds = time

    def _run(self, **kwargs):
        self._process_record.instance_state[self.CALC_NODE_LABEL] = \
            self._current_calc.uuid

        self._current_calc.submit()
        self._tick()
        while self._current_calc._is_running():
            time.sleep(self._poll_inteval)
            self._poll()

    def _on_process_continuing(self, record):
        from aiida.orm import load_node

        super(JobCalculation, self)._on_process_continuing(record)

        self._current_calc = \
            load_node(self._process_record.instance_state[self.CALC_NODE_LABEL])

        while self._current_calc._is_running():
            time.sleep(self._poll_inteval)
            self._poll()

    def _poll(self):
        """
        Update the states of calculations in WITHSCHEDULER status belonging
        to user and machine as defined in the 'dbauthinfo' table.
        """
        from aiida.orm import JobCalculation, Computer
        from aiida.utils.logger import get_dblogger_extra

        authinfo = self._current_calc._get_authinfo()
        if not authinfo.enabled:
            return

        # execlogger.debug("Updating running calc status for user {} "
        #                  "and machine {}".format(
        #     authinfo.aiidauser.email, authinfo.dbcomputer.name))

        scheduler = Computer(dbcomputer=authinfo.dbcomputer).get_scheduler()
        transport = authinfo.get_transport()
        logger_extra = get_dblogger_extra(self._current_calc)
        transport._set_logger_extra(logger_extra)

        try:
            state = self._current_calc.get_state()
            if state is calc_states.WITH_SCHEDULER:
                self._update_scheduler_status(
                    authinfo, transport, scheduler, logger_extra)
            elif state is calc_states.COMPUTED:
                self._retrieve_job(transport, logger_extra)
            elif state is calc_states.RETRIEVING:
                self._parse_step()
        except Exception:
            import traceback

            tb = traceback.format_exc()
            newextradict = logger_extra.copy()
            newextradict['full_traceback'] = tb
            if self._current_calc.get_state() == calc_states.PARSING:
                # execlogger.error("Error parsing calc {}. "
                #                  "Traceback: {}".format(calc.pk, tb),
                #                  extra=newextradict)
                # TODO: add a 'comment' to the calculation
                try:
                    self._current_calc._set_state(calc_states.PARSINGFAILED)
                except ModificationNotAllowed:
                    pass
            else:
                # execlogger.error("Error retrieving calc {}. "
                #                  "Traceback: {}".format(calc.pk, tb),
                #                  extra=newextradict)
                try:
                    self._current_calc._set_state(calc_states.RETRIEVALFAILED)
                except ModificationNotAllowed:
                    pass
                raise

    def _update_scheduler_status(self, authinfo, transport, scheduler, logger_extra):
        from aiida.orm import JobCalculation, Computer

        assert authinfo.enabled

        jobid = self._current_calc.get_job_id()
        with transport:
            scheduler.set_transport(transport)
            # TODO: Check if we are ok with filtering by job (to make this work,
            # I had to remove the check on the retval for getJobs,
            # because if the job has computed and is not in the output of
            # qstat, it gives a nonzero retval)

            # TODO: catch SchedulerError exception and do something
            # sensible (at least, skip this computer but continue with
            # following ones, and set a counter; set calculations to
            # UNKNOWN after a while?
            if scheduler.get_feature('can_query_by_user'):
                found_jobs = scheduler.getJobs(user="$USER", as_dict=True)
            else:
                found_jobs = scheduler.getJobs(jobs=[jobid], as_dict=True)

            # Update the status of the job
            try:
                if jobid is None:
                    # execlogger.error("JobCalculation {} is WITHSCHEDULER "
                    #                  "but no job id was found!".format(
                    #     c.pk), extra=logger_extra)
                    return

                # Check if the calculation to be checked (c)
                # is in the output of qstat
                if jobid in found_jobs:
                    # jobinfo: the information returned by
                    # qstat for this job
                    jobinfo = found_jobs[jobid]
                    # execlogger.debug("Inquirying calculation {} (jobid "
                    #                  "{}): it has job_state={}".format(
                    #     c.pk, jobid, jobinfo.job_state), extra=logger_extra)
                    # For the moment, FAILED is not defined
                    if jobinfo.job_state in [job_states.DONE]:  # , job_states.FAILED]:
                        computed = True

                    ## Do not set the WITHSCHEDULER state multiple times,
                    ## this would raise a ModificationNotAllowed
                    # else:
                    # c._set_state(calc_states.WITHSCHEDULER)

                    self._current_calc._set_scheduler_state(jobinfo.job_state)
                    self._current_calc._set_last_jobinfo(jobinfo)
                else:
                    # execlogger.debug("Inquirying calculation {} (jobid "
                    #                  "{}): not found, assuming "
                    #                  "job_state={}".format(
                    #     c.pk, jobid, job_states.DONE), extra=logger_extra)

                    # calculation c is not found in the output of qstat
                    computed = True
                    self._current_calc._set_scheduler_state(job_states.DONE)

            except Exception as e:
                # TODO: implement a counter, after N retrials
                # set it to a status that requires the user intervention
                # execlogger.warning("There was an exception for "
                #                    "calculation {} ({}): {}".format(
                #     c.pk, e.__class__.__name__, e.message),
                #                    extra=logger_extra)
                pass

            if computed:
                self._update_computed_jobinfo(scheduler)
                try:
                    self._current_calc._set_state(calc_states.COMPUTED)
                except ModificationNotAllowed:
                    # Someone already set it, just skip
                    pass

    def _update_computed_jobinfo(self, scheduler):
        from aiida.scheduler.datastructures import JobInfo

        jobid = self._current_calc.get_job_id()
        try:
            try:
                detailed_jobinfo = scheduler.get_detailed_jobinfo(jobid=jobid)
            except NotImplementedError:
                detailed_jobinfo = (
                    u"AiiDA MESSAGE: This scheduler does not implement "
                    u"the routine get_detailed_jobinfo to retrieve "
                    u"the information on "
                    u"a job after it has finished.")

            last_jobinfo = self._current_calc._get_last_jobinfo()
            if last_jobinfo is None:
                # Set it up appropriately
                last_jobinfo = JobInfo()
                last_jobinfo.job_id = jobid
                last_jobinfo.job_state = job_states.DONE

            last_jobinfo.detailedJobinfo = detailed_jobinfo
            self._current_calc._set_last_jobinfo(last_jobinfo)
        except Exception as e:
            # execlogger.warning("There was an exception while "
            #                    "retrieving the detailed jobinfo "
            #                    "for calculation {} ({}): {}".format(
            #     c.pk, e.__class__.__name__, e.message),
            #                    extra=logger_extra)
            pass

    def _retrieve_job(self, transport, logger_extra):
        from aiida.common.folders import SandboxFolder
        from aiida.orm.data.folder import FolderData
        from aiida.orm import DataFactory
        import os

        retrieved = False

        # Open connection
        with transport:
            calc = self._current_calc

            try:
                calc._set_state(calc_states.RETRIEVING)
            except ModificationNotAllowed:
                # Someone else has already started to retrieve it,
                # just log and continue
                # execlogger.debug("Attempting to retrieve more than once "
                #                  "calculation {}: skipping!".format(calc.pk),
                #                  extra=logger_extra)
                return retrieved

            # execlogger.debug("Retrieving calc {}".format(calc.pk),
            #                  extra=logger_extra)
            workdir = calc._get_remote_workdir()
            retrieve_list = calc._get_retrieve_list()
            retrieve_singlefile_list = calc._get_retrieve_singlefile_list()
            # execlogger.debug("[retrieval of calc {}] "
            #                  "chdir {}".format(calc.pk, workdir),
            #                  extra=logger_extra)
            transport.chdir(workdir)


            # First, retrieve the files of folderdata
            with SandboxFolder() as folder:
                retrieved_files = FolderData()
                for item in retrieve_list:
                    # I have two possibilities:
                    # * item is a string
                    # * or is a list
                    # then I have other two possibilities:
                    # * there are file patterns
                    # * or not
                    # First decide the name of the files
                    if isinstance(item, list):
                        tmp_rname, tmp_lname, depth = item
                        # if there are more than one file I do something differently
                        if transport.has_magic(tmp_rname):
                            remote_names = transport.glob(tmp_rname)
                            local_names = []
                            for rem in remote_names:
                                to_append = rem.split(os.path.sep)[-depth:] if depth > 0 else []
                                local_names.append(os.path.sep.join([tmp_lname] + to_append))
                        else:
                            remote_names = [tmp_rname]
                            to_append = remote_names.split(os.path.sep)[-depth:] if depth > 0 else []
                            local_names = [os.path.sep.join([tmp_lname] + to_append)]
                        if depth > 1:  # create directories in the folder, if needed
                            for this_local_file in local_names:
                                new_folder = os.path.join(
                                    folder.abspath,
                                    os.path.split(this_local_file)[0])
                                if not os.path.exists(new_folder):
                                    os.makedirs(new_folder)
                    else:  # it is a string
                        if transport.has_magic(item):
                            remote_names = transport.glob(item)
                            local_names = [os.path.split(rem)[1] for rem in remote_names]
                        else:
                            remote_names = [item]
                            local_names = [os.path.split(item)[1]]

                    for rem, loc in zip(remote_names, local_names):
                        # execlogger.debug("[retrieval of calc {}] "
                        #                  "Trying to retrieve remote item '{}'".format(
                        #     calc.pk, rem),
                        #                  extra=logger_extra)
                        transport.get(rem, os.path.join(folder.abspath, loc),
                                      ignore_nonexisting=True)

                # Here I retrieved everything;
                # now I store them inside the calculation
                retrieved_files.replace_with_folder(folder.abspath,
                                                    overwrite=True)
                self._out(calc._get_linkname_retrieved(), retrieved_files)
                # execlogger.debug("[retrieval of calc {}] "
                #                  "Storing retrieved_files={}".format(
                #     calc.pk, retrieved_files.dbnode.pk),
                #     extra=logger_extra)

            # Second, retrieve the singlefiles
            with SandboxFolder() as folder:
                singlefile_list = []
                for (linkname, subclassname, filename) in retrieve_singlefile_list:
                    # execlogger.debug("[retrieval of calc {}] Trying "
                    #                  "to retrieve remote singlefile '{}'".format(
                    #     calc.pk, filename),
                    #                  extra=logger_extra)
                    localfilename = os.path.join(
                        folder.abspath, os.path.split(filename)[1])
                    transport.get(filename, localfilename,
                                  ignore_nonexisting=True)
                    singlefile_list.append((linkname, subclassname,
                                            localfilename))

                # ignore files that have not been retrieved
                singlefile_list = [i for i in singlefile_list if
                                   os.path.exists(i[2])]

                # after retrieving from the cluster, create the objects
                for (linkname, subclassname, filename) in singlefile_list:
                    SinglefileSubclass = DataFactory(subclassname)
                    singlefile = SinglefileSubclass()
                    singlefile.set_file(filename)
                    self._out(linkname, singlefile)
                    # execlogger.debug("[retrieval of calc {}] "
                    #                  "Storing retrieved_singlefile={}".format(
                    #     calc.pk, singlefile.dbnode.pk),
                    #                  extra=logger_extra)

            retrieved = True

        return retrieved

    def _parse_step(self):
        calc = self._current_calc
        calc._set_state(calc_states.PARSING)

        Parser = calc.get_parserclass()
        # If no parser is set, the calculation is successful
        successful = True
        if Parser is not None:
            parser = Parser(calc)
            successful, new_nodes_tuple = parser.parse_from_calc()

            for label, n in new_nodes_tuple:
                self._out(label, n)

        if successful:
            try:
                calc._set_state(calc_states.FINISHED)
            except ModificationNotAllowed:
                # I should have been the only one to set it, but
                # in order to avoid useless error messages, I
                # just ignore
                pass
        else:
            try:
                calc._set_state(calc_states.FAILED)
            except ModificationNotAllowed:
                # I should have been the only one to set it, but
                # in order to avoid useless error messages, I
                # just ignore
                pass
                # execlogger.error("[parsing of calc {}] "
                #                  "The parser returned an error, but it should have "
                #                  "created an output node with some partial results "
                #                  "and warnings. Check there for more information on "
                #                  "the problem".format(calc.pk), extra=logger_extra)
        return successful

    def _create_db_record(self):
        return self._CALC_CLASS()

    def _setup_db_record(self, inputs):
        from aiida.common.links import LinkType

        # Link and store the retrospective provenance for this process
        calc = self._create_db_record()  # (unstored)
        assert (not calc.is_stored)

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in inputs.iteritems():
            if isinstance(self.spec().get_input(name), port.InputGroupPort):
                additional =\
                    self._CALC_CLASS._use_methods[name]['additional_parameter']

                for k, v in input.iteritems():
                    getattr(calc, 'use_{}'.format(name))(input, **{additional: v})

            else:
                getattr(calc, 'use_{}'.format(name))(input)

        if self._parent:
            calc.add_link_from(self._parent._current_calc, "CALL", LinkType.CALL)

        if self._computer:
            calc.set_computer(self._computer)

        if self._resources:
            calc.set_resources(self._resources)

        if self._custom_scheduler_commands:
            calc.set_custom_scheduler_commands(self._custom_scheduler_commands)

        if self._queue_name:
            calc.set_queue_name(self._queue_name)

        if self._resources:
            calc.set_resources(self._resources)

        if self._max_wallclock_seconds:
            calc.set_max_wallclock_seconds(self._max_wallclock_seconds)

        self._current_calc = calc
        self._current_calc.store()

import re
from collections import namedtuple
import threading
import plum.event
from plum.event import EventEmitter, WithProcessEvents, PollingEmitter
from aiida.common.lang import override
from aiida.common.datastructures import calc_states
from aiida.orm import load_node
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.calculation import Calculation
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.work import WorkCalculation
from aiida.backends.utils import get_authinfo
from aiida.scheduler.datastructures import job_states
from aiida.transport import get_transport_queue


class DbPollingEmitter(PollingEmitter, WithProcessEvents):
    PK_REGEX = re.compile('calc\.(.+)\.(.+)')
    DEFAULT_POLL_INTERVAL = 30  # seconds

    def __init__(self, poll_interval=DEFAULT_POLL_INTERVAL):
        super(DbPollingEmitter, self).__init__(poll_interval)

    @override
    def start_listening(self, listener, event='*'):
        if not event.startswith("calc."):
            raise ValueError(
                "This emitter only knows about calc.[pk].[event] events")
        super(DbPollingEmitter, self).start_listening(listener, event)

    @override
    def poll(self):
        pk_events = {}
        for e in self._specific_listeners.iterkeys():
            m = self.PK_REGEX.match(e)
            pk_events.setdefault(int(m.group(1)), set()).add(m.group(2))

        q = QueryBuilder()
        q.append(
            Calculation,
            filters={
                'id': {'in': pk_events.keys()},
                'or': [
                    {'attributes': {'has_key': WorkCalculation.FAILED_KEY}},
                    {'attributes.{}'.format(WorkCalculation.FINISHED_KEY): True}
                ]
            },
            project=[
                'id',
                'attributes.{}'.format(WorkCalculation.FAILED_KEY),
                'attributes.{}'.format(WorkCalculation.FINISHED_KEY)
            ]
        )
        for r in q.all():
            if r[2]:
                self.event_occurred("calc.{}.finished".format(r[0]))
                self.event_occurred("calc.{}.stopped".format(r[0]))
            elif r[1] is not None:
                self.event_occurred("calc.{}.failed".format(r[0]))


class ProcessMonitorEmitter(plum.event.ProcessMonitorEmitter):
    @override
    def on_monitored_process_finish(self, process):
        super(ProcessMonitorEmitter, self).on_monitored_process_finish(process)
        self._calc_event_occurred(process.calc.pk, "finished")

    @override
    def on_monitored_process_stopped(self, process):
        super(ProcessMonitorEmitter, self).on_monitored_process_stopped(process)
        self._calc_event_occurred(process.calc.pk, "stopped")

    @override
    def on_monitored_process_failed(self, process):
        super(ProcessMonitorEmitter, self).on_monitored_process_failed(process)
        self._calc_event_occurred(process.calc.pk, "failed")

    def _calc_event_occurred(self, pk, evt):
        self.event_occurred("calc.{}.{}".format(pk, evt))


class _PeriodicTimer(threading.Thread):
    def __init__(self, interval, fn):
        super(_PeriodicTimer, self).__init__()
        self.daemon = True

        self._interval = interval
        self._timeout = interval
        self._fn = fn
        self._interrupt = threading.Condition()
        self._shutdown = False

    def run(self):
        with self._interrupt:
            while True:
                if self._timeout is not None:
                    self._fn()
                self._interrupt.wait(self._timeout)
                if self._shutdown:
                    break

    def pause(self):
        assert not self._shutdown, "Timer has been shut down"

        self._timeout = None

    def play(self):
        assert not self._shutdown, "Timer has been shut down"

        with self._interrupt:
            self._timeout = self._interval
            self._interrupt.notify_all()

    def shutdown(self):
        assert not self._shutdown, "Timer has been shut down"

        with self._interrupt:
            self._shutdown = True
            self._interrupt.notify_all()


class SchedulerEmitter(EventEmitter):
    JOB_NOT_FOUND = "NOT_FOUND"
    DEFAULT_POLL_INTERVAL = 30  # seconds

    Entry = namedtuple("Entry", ['scheduler', 'jobs'])

    class JobData(object):
        def __init__(self, pk, current_state):
            self.pk = pk
            self.current_state = current_state

    def __init__(self, poll_interval=DEFAULT_POLL_INTERVAL):
        super(SchedulerEmitter, self).__init__()
        self._pending_calcs = set()
        self._entries = {}
        self._poll_timer = _PeriodicTimer(poll_interval, self._poll)

    def start_listening(self, listener, event='*'):
        pk_string = self._extract_pk_string(event)
        super(SchedulerEmitter, self).start_listening(listener, event)

        pk = int(pk_string)
        try:
            self._add_calc(load_node(pk))
        except ValueError:
            self._pending_calcs.add(pk)
            self._ensure_polling()

    @staticmethod
    def _extract_pk_string(event):
        if not event.startswith("job."):
            raise ValueError(
                "This emitter only knows about job.<pk>[.event] events")

        pk_string = event.split('.')[1]
        if len(pk_string) == 0:
            raise ValueError(
                "You must supply an event in the format 'job.<pk>[.event]' "
                "where pk can be a pk or a wildcard.\nGot '{}'".format(event)
            )

        if SchedulerEmitter.contains_wildcard(pk_string):
            raise ValueError(
                "You cannot use a wildcard in the pk_string at the moment.\n"
                "Got: '{}'".format(pk_string)
            )

        return pk_string

    def _do_update_for_scheduler(self, authinfo, transport):
        auth_id = authinfo.id
        entry = self._entries[auth_id]
        scheduler = entry.scheduler
        scheduler.set_transport(transport)

        # Get all jobs except for those that are already done,
        # their state won't change anyway
        jobs_to_inquire = self._get_active_job_ids(auth_id)
        if len(jobs_to_inquire) == 0:
            return

        found_jobs = self._get_scheduler_jobs(scheduler, jobs_to_inquire)
        for job_id in jobs_to_inquire:
            job_data = entry.jobs[job_id]
            info = found_jobs.get(job_id, None)
            if info is None:
                current_state = self.JOB_NOT_FOUND
            else:
                current_state = info.job_state

            # Has the state changed since last polling?
            if current_state != job_data.current_state:
                job_data.current_state = current_state

                # Send the message with the information from the scheduler
                # as the body
                body = {'job_info': info}
                # If the job is done, also get detailed job info
                if current_state == job_states.DONE:
                    try:
                        detailed = scheduler.get_detailed_jobinfo(job_id)
                    except NotImplementedError:
                        detailed = (
                            u"AiiDA MESSAGE: This scheduler does not implement "
                            u"the routine get_detailed_jobinfo to retrieve "
                            u"the information on "
                            u"a job after it has finished.")

                    body['detailed_job_info'] = detailed

                self.event_occurred(
                    "job.{}.{}".format(job_data.pk, job_data.current_state), body)

        # Should we keep polling this scheduler?
        if len(self._get_active_job_ids(auth_id)) > 0:
            get_transport_queue().call_me_with_transport(
                authinfo, self._do_update_for_scheduler)

    def _get_active_job_ids(self, auth_id):
        """
        Get a list of all the job ids that aren't in the DONE state

        :param auth_id: The authentication info id
        :return: A lit of all the active job ids
        :rtype: list
        """
        entry = self._entries[auth_id]
        return [
            job_id for job_id, job_data in
            entry.jobs.iteritems() if
            job_data.current_state != job_states.DONE
        ]

    def _get_scheduler_jobs(self, scheduler, job_ids):
        if len(job_ids) == 0:
            return []

        if scheduler.get_feature('can_query_by_user'):
            found_jobs = scheduler.getJobs(user="$USER", as_dict=True)
        else:
            found_jobs = scheduler.getJobs(jobs=job_ids, as_dict=True)

        return found_jobs

    def _poll(self):
        if len(self._pending_calcs) == 0:
            return

        qb = QueryBuilder()
        qb.append(
            JobCalculation,
            filters={
                'id': {'in': self._pending_calcs},
                'state': {'==': calc_states.WITHSCHEDULER}
            }
        )

        for res in qb.all():
            calc = res[0]
            try:
                self._add_calc(calc)
                self._pending_calcs.remove(calc.pk)
            except ValueError:
                pass

        if len(self._pending_calcs) > 0:
            self._ensure_polling()
        else:
            self._poll_timer.pause()

    def _ensure_polling(self):
        if self._poll_timer.is_alive():
            self._poll_timer.play()
        else:
            self._poll_timer.start()

    def _add_calc(self, calc):
        job_id = calc.get_job_id()
        if job_id is None:
            raise ValueError("Calculation has no job id")

        computer = calc.get_computer()
        user = calc.get_user()
        authinfo = get_authinfo(computer, user)

        entry = self._entries.get(authinfo.id, None)
        if entry is None:
            entry = self.Entry(computer.get_scheduler(), {})
            self._entries[authinfo.id] = entry
        entry.jobs[job_id] = self.JobData(calc.pk, None)

        if len(self._get_active_job_ids(authinfo.id)) > 0:
            get_transport_queue().call_me_with_transport(
                authinfo, self._do_update_for_scheduler)
        return entry

    def _remove_job(self, auth_id, job_id):
        entry = self._entries[auth_id]
        del entry.jobs[job_id]
        if len(entry.jobs) == 0:
            del self._entries[auth_id]

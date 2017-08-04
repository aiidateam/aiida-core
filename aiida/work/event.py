import apricotpy
import re

from aiida.backends.utils import get_authinfo
from aiida.common.lang import override
from aiida.orm import load_node
from aiida.orm.calculation import Calculation
from aiida.orm.calculation.work import WorkCalculation
from aiida.orm.querybuilder import QueryBuilder
from aiida.scheduler.datastructures import job_states
from . import transport

#
# class DbPollingEmitter(apricotpy.LoopObject):
#     """
#     Emits loop messages about calculations in the database
#     """
#     PK_REGEX = re.compile('calc\.(.+)\.(.+)')
#     DEFAULT_POLL_INTERVAL = 30  # seconds
#
#     def __init__(self, loop, poll_interval=DEFAULT_POLL_INTERVAL):
#         super(DbPollingEmitter, self).__init__(loop)
#
#         self._poll_interval = poll_interval
#         self._callback_handle = None
#
#     @override
#     def on_loop_inserted(self, loop):
#         super(DbPollingEmitter, self).on_loop_inserted(loop)
#
#         # Listen for anyone that wants to know about calculations
#         loop.messages().add_listener(self._listener_changed, 'mailman.listener_*.calc.*')
#
#         if self._should_poll():
#             self._callback_handle = self.loop().call_soon(self._poll)
#
#     @override
#     def on_loop_removed(self):
#         self.loop().messages.remove_listener(self._listener_changed)
#
#         if self._callback_handle is not None:
#             self._callback_handle.cancel()
#             self._callback_handle = None
#
#         super(DbPollingEmitter, self).on_loop_removed()
#
#     def _poll(self):
#         self._callback_handle = None
#         self._do_poll()
#         self._update_polling()
#
#     def _do_poll(self):
#         messages = self.loop().messages()
#         pk_events = {}
#         for e in messages.specific_listeners().iterkeys():
#             match = self.PK_REGEX.match(e)
#             if match is not None:
#                 pk_events.setdefault(int(match.group(1)), set()).add(match.group(2))
#
#         q = QueryBuilder()
#         q.append(
#             Calculation,
#             filters={
#                 'id': {'in': pk_events.keys()},
#                 'or': [
#                     {'attributes': {'has_key': WorkCalculation.FAILED_KEY}},
#                     {'attributes.{}'.format(WorkCalculation.FINISHED_KEY): True}
#                 ]
#             },
#             project=[
#                 'id',
#                 'attributes.{}'.format(WorkCalculation.FAILED_KEY),
#                 'attributes.{}'.format(WorkCalculation.FINISHED_KEY)
#             ]
#         )
#         for r in q.all():
#             if r[2]:
#                 messages.send("calc.{}.finished".format(r[0]))
#                 messages.send("calc.{}.stopped".format(r[0]))
#             elif r[1] is not None:
#                 messages.send("calc.{}.failed".format(r[0]))
#
#     def _listener_changed(self, loop, subject, body):
#         self._update_polling()
#
#     def _update_polling(self):
#         if self._should_poll():
#             if self._callback_handle is None:
#                 self._callback_handle = self.loop().call_later(self._poll_interval, self._poll)
#         else:
#             if self._callback_handle is not None:
#                 self._callback_handle.cancel()
#                 self._callback_handle = None
#
#     def _should_poll(self):
#         for e in self.loop().messages().specific_listeners().iterkeys():
#             if self.PK_REGEX.match(e) is not None:
#                 return True
#
#         return False


class GetSchedulerUpdate(apricotpy.PersistableTask):
    """
    This task will get a scheduler update for the given job
    """

    def __init__(self, loop, calc, authinfo, last_state=None):
        super(GetSchedulerUpdate, self).__init__(loop)

        self._updated = None
        self._calc = calc
        self._authinfo = authinfo
        self._callback_handle = None
        self._last_state = last_state

        if self._calc.get_job_id() is None:
            raise ValueError("Calculation has no job id")

    def execute(self):
        self._updated = self.loop().create_futrue()
        self._callback_handle = transport.call_me_with_transport(
            self.loop(), self._authinfo, self._submit_calc)
        return apricotpy.Await(self._updated)

    def save_instance_state(self, out_state):
        super(GetSchedulerUpdate, self).save_instance_state(out_state)
        out_state['calc_pk'] = self._calc.pk
        out_state['last_state'] = self._last_state

    def load_instance_state(self, loop, saved_state):
        super(GetSchedulerUpdate, self).load_instance_state(loop, saved_state)

        self._updated = loop.create_future()
        self._calc = load_node(saved_state['calc_pk'])
        self._authinfo = get_authinfo(self._calc.get_computer(), self._calc.get_user())
        self._callback_handle = None
        self._last_state = saved_state['last_state']

    def _get_scheduler_update(self, authinfo, trans):
        scheduler = self._calc.get_computer().get_scheduler()
        scheduler.set_transport(trans)

        job_id = self._calc.get_job_id()

        kwargs = {'jobs': [job_id], 'as_dict': True}
        if scheduler.get_feature('can_query_by_user'):
            kwargs['user'] = "$USER"
        found_jobs = scheduler.getJobs(**kwargs)

        info = found_jobs.get(job_id, None)
        if info is None:
            current_state = self.JOB_NOT_FOUND
        else:
            current_state = info.job_state

        # Has the state changed since what the user supplied?
        if self._last_state is None or self._last_state is job_states.DONE \
                or current_state != self._last_state:
            info = {'job_info': info}
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

                info['detailed_job_info'] = detailed

            self._updated.set_result(info)
        else:
            self._callback_handle = transport.call_me_with_transport(self.loop(), self._authinfo, self._submit_calc)

from aiida.scheduler.datastructures import job_states
from aiida.work import transport
from apricotpy import persistable

from aiida.backends.utils import get_authinfo
from aiida.common.datastructures import calc_states
from aiida.daemon import execmanager
from aiida.orm import load_node
from aiida.work.transport import call_me_with_transport


class SubmitCalc(persistable.Task):
    """
    Take a job calculation and submit it.
    """

    CALC_PK = 'CALC_PK'

    def __init__(self, calc, authinfo):
        super(SubmitCalc, self).__init__()

        self._calc = calc
        self._authinfo = authinfo

        # Runtime state
        self._callback_handle = None

    def execute(self):
        self._callback_handle = \
            call_me_with_transport(self.loop(), self._authinfo, self._submit_calc)

        return self.loop().create_future()

    def on_loop_removed(self):
        super(SubmitCalc, self).on_loop_removed()

        if self._callback_handle is not None:
            self._callback_handle.cancel()
            self._callback_handle = None

    def save_instance_state(self, out_state):
        super(SubmitCalc, self).save_instance_state(out_state)
        out_state['calc_pk'] = self._calc.pk

    def load_instance_state(self, saved_state):
        super(SubmitCalc, self).load_instance_state(saved_state)

        self._calc = load_node(saved_state[self.CALC_PK])

        # Runtime state
        self._authinfo = get_authinfo(self._calc.get_computer(), self._calc.get_user())
        if not self.done() and self.awaiting() is not None:
            self._callback_handle = \
                call_me_with_transport(self.loop(), self._authinfo, self._submit_calc)
        else:
            self._callback_handle = None

    def _submit_calc(self, authinfo, transport):
        if self._calc.state != calc_states.SUBMITTING:
            self._calc._set_state(calc_states.SUBMITTING)
        try:
            execmanager.submit_calc(self._calc, authinfo, transport)
        except BaseException as e:
            self.awaiting().set_exception(e)
        else:
            self.awaiting().set_result(True)


class RetrieveCalc(persistable.Task):
    """
    Take a finished job calculation and retrieve from the supercomputer.
    """
    CALC_PK = 'CALC_PK'

    def __init__(self, calc, authinfo):
        super(RetrieveCalc, self).__init__()

        self._calc = calc
        self._authinfo = authinfo

        # Runtime state
        self._callback_handle = None

    def execute(self):
        self._callback_handle = \
            call_me_with_transport(self.loop(), self._authinfo, self._retrieve_calc)

        return self.loop().create_future()

    def on_loop_removed(self):
        super(RetrieveCalc, self).on_loop_removed()

        if self._callback_handle is not None:
            self._callback_handle.cancel()
            self._callback_handle = None

    def save_instance_state(self, out_state):
        super(RetrieveCalc, self).save_instance_state(out_state)
        out_state[self.CALC_PK] = self._calc.pk

    def load_instance_state(self, saved_state):
        super(RetrieveCalc, self).load_instance_state(saved_state)

        self._calc = load_node(saved_state[self.CALC_PK])

        # Runtime state
        self._authinfo = get_authinfo(self._calc.get_computer(), self._calc.get_user())
        if not self.done() and self.awaiting() is not None:
            self._callback_handle = \
                call_me_with_transport(self.loop(), self._authinfo, self._retrieve_calc)
        else:
            self._callback_handle = None

    def _retrieve_calc(self, authinfo, transport):
        if self._calc.state != calc_states.RETRIEVING:
            self._calc._set_state(calc_states.RETRIEVING)
        try:
            execmanager.retrieve_all(self._calc, authinfo, transport)
        except BaseException as e:
            self._calc._set_state(calc_states.RETRIEVALFAILED)
            self.awaiting().set_exception(e)
        else:
            self.awaiting().set_result(True)


class GetSchedulerUpdate(persistable.Task):
    """
    This task will get a scheduler update for the given job
    """
    CALC_PK = 'CALC_PK'
    LAST_STATE = 'LSAT_STATE'
    CALLBACK_HANDLE = 'CALLBACK_HANDLE'

    def __init__(self, calc, authinfo, last_state=None):
        super(GetSchedulerUpdate, self).__init__()

        self._calc = calc
        self._last_state = last_state

        # Instance state (not need to persist):
        self._authinfo = authinfo
        self._callback_handle = None

        if self._calc.get_job_id() is None:
            raise ValueError("Calculation has no job id")

    def execute(self):
        self._callback_handle = transport.call_me_with_transport(
            self.loop(), self._authinfo, self._get_scheduler_update)

        return self.loop().create_future()

    def on_loop_removed(self):
        super(GetSchedulerUpdate, self).on_loop_removed()

        if self._callback_handle is not None:
            self._callback_handle.cancel()
            self._callback_handle = None

    def save_instance_state(self, out_state):
        super(GetSchedulerUpdate, self).save_instance_state(out_state)

        out_state[self.CALC_PK] = self._calc.pk
        out_state[self.LAST_STATE] = self._last_state

    def load_instance_state(self, saved_state):
        super(GetSchedulerUpdate, self).load_instance_state(saved_state)

        self._calc = load_node(saved_state['calc_pk'])
        self._last_state = saved_state['last_state']

        self._authinfo = get_authinfo(self._calc.get_computer(), self._calc.get_user())

        if not self.done() and self.awaiting() is not None:
            self._callback_handle = transport.call_me_with_transport(
                self.loop(), self._authinfo, self._get_scheduler_update)
        else:
            self._callback_handle = None

    def _get_scheduler_update(self, authinfo, trans):
        self._callback_handle = None

        scheduler = self._calc.get_computer().get_scheduler()
        scheduler.set_transport(trans)

        job_id = self._calc.get_job_id()

        kwargs = {'jobs': [job_id], 'as_dict': True}
        if scheduler.get_feature('can_query_by_user'):
            kwargs['user'] = "$USER"
        found_jobs = scheduler.getJobs(**kwargs)

        info = found_jobs.get(job_id, None)
        if info is None:
            # TODO: Check this is the right thing to set this to
            current_state = None
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

            self.awaiting().set_result(info)
        else:
            self._callback_handle = \
                transport.call_me_with_transport(self.loop(), self._authinfo,
                                                 self._get_scheduler_update)

import plum.loop.persistence
from plum.loop import tasks
from aiida.backends.utils import get_authinfo
from aiida.common.datastructures import calc_states
from aiida.daemon import execmanager
from aiida.orm import load_node
from aiida.work.transport import call_me_with_transport


class SubmitCalc(plum.loop.persistence.PersistableTask):
    def __init__(self, loop, calc, authinfo):
        super(SubmitCalc, self).__init__(loop)

        self._submitted = loop.create_future()
        self._calc = calc
        self._authinfo = authinfo
        self._callback_handle = None

    def save_instance_state(self, out_state):
        super(SubmitCalc, self).save_instance_state(out_state)
        out_state['calc_pk'] = self._calc.pk

    def load_instance_state(self, saved_state, loop):
        super(SubmitCalc, self).load_instance_state(saved_state, loop)

        self._submitted = loop.create_future()
        self._calc = load_node(saved_state['calc_pk'])
        self._authinfo = get_authinfo(self._calc.get_computer(), self._calc.get_user())
        self._callback_handle = None

    def execute(self):
        self._callback_handle = call_me_with_transport(self.loop(), self._authinfo, self._submit_calc)
        return tasks.Await(self._submitted)

    def _submit_calc(self, authinfo, transport):
        if self._calc.state != calc_states.SUBMITTING:
            self._calc._set_state(calc_states.SUBMITTING)
        try:
            execmanager.submit_calc(self._calc, authinfo, transport)
        except BaseException as e:
            self._submitted.set_exception(e)
        else:
            self._submitted.set_result(True)


class RetrieveCalc(plum.loop.persistence.PersistableTask):
    def __init__(self, loop, calc, authinfo):
        super(RetrieveCalc, self).__init__(loop)

        self._retrieved = loop.create_future()
        self._calc = calc
        self._authinfo = authinfo
        self._callback_handle = None

    def save_instance_state(self, out_state):
        super(RetrieveCalc, self).save_instance_state(out_state)
        out_state['calc_pk'] = self._calc.pk

    def load_instance_state(self, loop, saved_state):
        super(RetrieveCalc, self).load_instance_state(saved_state, loop)

        self._retrieved = loop.create_future()
        self._calc = load_node(saved_state['calc_pk'])
        self._authinfo = get_authinfo(self._calc.get_computer(), self._calc.get_user())
        self._callback_handle = None

    def execute(self):
        self._callback_handle = call_me_with_transport(self.loop(), self._authinfo, self._retrieve_calc)
        return tasks.Await(self._retrieved)

    def _retrieve_calc(self, authinfo, transport):
        if self._calc.state != calc_states.RETRIEVING:
            self._calc._set_state(calc_states.RETRIEVING)
        try:
            execmanager.retrieve_all(self._calc, authinfo, transport)
        except BaseException as e:
            self._retrieved.set_exception(e)
            self._calc._set_state(calc_states.RETRIEVALFAILED)
        else:
            self._retrieved.set_result(True)

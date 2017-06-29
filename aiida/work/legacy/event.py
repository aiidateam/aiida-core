import re
from plum.event import PollingEmitter
from aiida.orm import load_workflow
from aiida.common.datastructures import wf_states
from aiida.common.lang import override

WORKFLOW_POLL_INTERVAL = 30.  # seconds


class WorkflowEmitter(PollingEmitter):
    PK_REGEX = re.compile('legacy_workflow\.(.+)')

    def __init__(self, poll_interval=WORKFLOW_POLL_INTERVAL):
        super(WorkflowEmitter, self).__init__(poll_interval)

    @override
    def start_listening(self, listener, event='*'):
        if not event.startswith('legacy_workflow.'):
            raise ValueError(
                "This emitter only knows about legacy_workflow.[pk] events"
            )
        super(WorkflowEmitter, self).start_listening(listener, event)

    @override
    def poll(self):
        # Poll here
        pks = set()
        for e in self._specific_listeners.iterkeys():
            m = self.PK_REGEX.match(e)
            pks.add(int(m.group(1)))

        for pk in pks:
            wf = load_workflow(pk=pk)
            state = wf.get_state()

            if state in [wf_states.FINISHED, wf_states.ERROR]:
                self.event_occurred(
                    "legacy_workflow.{}.{}".format(pk, str(state).lower()))

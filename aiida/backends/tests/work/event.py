
import threading
from aiida.backends.testbase import AiidaTestCase
from aiida.work.globals import get_event_emitter
from aiida.work.event import DbPollingEmitter
import aiida.work.util as util
from aiida.work.test_utils import DummyProcess


class TestDbPollingTracker(AiidaTestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(get_event_emitter().num_listening(), 0)
        self.emitter = DbPollingEmitter(1.0)
        self.notified_events = set()
        self.event_received = threading.Event()

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(get_event_emitter().num_listening(), 0)

    def test_simple_event(self):
        dp = DummyProcess.new()
        evt = "calc.{}.finished".format(dp.pid)

        with self.emitter.listen_scope(self._notify, evt):
            dp.start()
            self.assertTrue(self.event_received.wait(2.), "Did not get message in time")

        self.assertTrue(evt in self.notified_events)

    def test_stop_listening(self):
        """
        Make sure we don't get the event after we've said we don't want to
        listen anymore
        """
        dp = DummyProcess.new()
        evt = "calc.{}.finished".format(dp.pid)

        self.emitter.start_listening(self._notify, evt)
        self.emitter.stop_listening(self._notify, evt)
        dp.start()
        self.assertFalse(self.event_received.is_set())

    def _notify(self, emitter, event, body):
        self.notified_events.add(event)
        self.event_received.set()


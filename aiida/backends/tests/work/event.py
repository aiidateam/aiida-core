from aiida.backends.testbase import AiidaTestCase
from aiida.work.event import DbPollingEmitter
import aiida.work.utils as util
from aiida.work.test_utils import DummyProcess
from plum.loop import BaseEventLoop
from aiida.work.run import enqueue, run_loop


class TestDbPollingTracker(AiidaTestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

        self.loop = BaseEventLoop()
        self.loop.create(DbPollingEmitter, 1.0)
        self.notified_events = set()
        self.event_received = False

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_simple_event(self):
        dp = enqueue(DummyProcess)
        evt = "process.{}.finish".format(dp.pid)

        with self.loop.messages().listen_scope(self._notify, evt):
            run_loop()
            self.assertTrue(self.event_received, "Did not get message")

        self.assertTrue(evt in self.notified_events)

    def test_stop_listening(self):
        """
        Make sure we don't get the event after we've said we don't want to
        listen anymore
        """
        dp = enqueue(DummyProcess)
        evt = "process.{}.finished".format(dp.pid)

        self.loop.messages().add_listener(self._notify, evt)
        self.loop.messages().remove_listener(self._notify, evt)
        run_loop()
        self.assertFalse(self.event_received)

    def _notify(self, emitter, event, body):
        self.notified_events.add(event)
        self.event_received = True

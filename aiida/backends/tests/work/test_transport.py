from tornado.gen import coroutine, Return

from aiida.backends.testbase import AiidaTestCase
from aiida.work.transports import TransportQueue


class TestTransportQueue(AiidaTestCase):
    """ Tests for the transport queue """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """ Set up a simple authinfo and for later use """
        super(TestTransportQueue, cls).setUpClass(*args, **kwargs)
        # Configure the computer - no parameters for local transport
        # WARNING: This is not deleted as there is no API facing way to do this
        # it would require a backend specific call
        cls.authinfo = cls.backend.authinfos.create(
            computer=cls.computer,
            user=cls.backend.users.get_automatic_user())
        cls.authinfo.store()

    def test_simple_request(self):
        """ Test a simple transport request """
        queue = TransportQueue()
        loop = queue.loop()

        @coroutine
        def test():
            trans = None
            with queue.request_transport(self.authinfo) as request:
                trans = yield request
                self.assertTrue(trans.is_open)
            self.assertFalse(trans.is_open)

        loop.run_sync(lambda: test())

    def test_get_transport_nested(self):
        """ Test nesting calls to get the same transport """
        transport_queue = TransportQueue()
        loop = transport_queue.loop()

        @coroutine
        def nested(queue, authinfo):
            with queue.request_transport(authinfo) as request1:
                trans1 = yield request1
                self.assertTrue(trans1.is_open)
                with queue.request_transport(authinfo) as request2:
                    trans2 = yield request2
                    self.assertIs(trans1, trans2)
                    self.assertTrue(trans2.is_open)

        loop.run_sync(lambda: nested(transport_queue, self.authinfo))

    def test_get_transport_interleaved(self):
        """ Test interleaved calls to get the same transport """
        transport_queue = TransportQueue()
        loop = transport_queue.loop()

        @coroutine
        def interleaved(authinfo):
            with transport_queue.request_transport(authinfo) as trans_future:
                yield trans_future

        loop.run_sync(lambda: [interleaved(self.authinfo), interleaved(self.authinfo)])

    def test_return_from_context(self):
        """ Test raising a Return from coroutine context """
        queue = TransportQueue()
        loop = queue.loop()

        @coroutine
        def test():
            with queue.request_transport(self.authinfo) as request:
                trans = yield request
                raise Return(trans.is_open)

        retval = loop.run_sync(lambda: test())
        self.assertTrue(retval)

from aiida.backends.testbase import AiidaTestCase
from aiida import work
import aiida.work.test_utils

from . import utils


class TestWf(AiidaTestCase):
    def test_calculation_future_broadcasts(self):
        runner = utils.create_test_runner(with_communicator=True)
        proc = work.test_utils.DummyProcess()
        # No polling
        future = work.CalculationFuture(
            pk=proc.pid,
            poll_interval=None,
            communicator=runner.communicator)
        work.run(proc)
        calc_node = runner.run_until_complete(future)
        self.assertEqual(proc.calc.pk, calc_node.pk)

    def test_calculation_future_polling(self):
        runner = utils.create_test_runner()
        proc = work.test_utils.DummyProcess()
        # No communicator
        future = work.CalculationFuture(
            pk=proc.pid,
            loop=runner.loop,
            poll_interval=0)
        work.run(proc)
        calc_node = runner.run_until_complete(future)
        self.assertEqual(proc.calc.pk, calc_node.pk)



from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import click
import threading
from aiida.work.event import SchedulerEmitter


def _print_evt(emitter, event):
    print(event)


@click.command()
@click.option('--pk', help='pk of the calculation to print scheduler events for')
@click.option('--poll', type=float, help='sets the poll interval in seconds')
def print_events(pk, poll):
    emitter = SchedulerEmitter(poll_interval=poll)
    emitter.start_listening(_print_evt, 'job.{}.*'.format(pk))
    threading.Event().wait()


if __name__ == '__main__':
    print_events()

#!/usr/bin/env python
from __future__ import division
import sys

from aiida.common.utils import load_django
load_django()

import datetime, pytz

from django.db.models import Q
from aiida.orm import Calculation
from aiida.common.datastructures import calc_states

failed_states = [calc_states.SUBMISSIONFAILED, calc_states.RETRIEVALFAILED, calc_states.PARSINGFAILED,
                 calc_states.UNDETERMINED, calc_states.FAILED]
finished_states = [calc_states.FINISHED]
new_states = [calc_states.NEW]
processing_states = list(set(calc_states)-set(failed_states + finished_states + new_states))

mapping = {
    '--failed': failed_states,
    '--finished': finished_states,
    '--new': new_states,
    '--processing': processing_states,
    '--all': list(calc_states),
}

try:
    whichstr = sys.argv[1]
    try:
        calc_states_set = mapping[whichstr]
    except KeyError:
        print >> sys.stderr, "Invalid command. Can be only one of the following:"
        for i in sorted(mapping.keys()):
            print >> sys.stderr, " ", i
        sys.exit(1)
except IndexError:
    calc_states_set = processing_states

calclist = Calculation.query(attributes__tval__in=calc_states_set,
                             attributes__key="_state").distinct().order_by('ctime')

now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
for c in calclist:
    time_ago = c.dbnode.ctime - now
    if time_ago > datetime.timedelta(0):
        time_str = str(c.dbnode.ctime) + ('[in the future??]')
    else:
        time_ago = - time_ago
        days = time_ago.days
        hours = time_ago.seconds // 3600
        minutes = (time_ago.seconds // 60 ) % 60
        seconds = time_ago.seconds % 60
        string_pieces = []
        if days > 0:
            string_pieces.append('{} {}'.format(days, "day" if days == 1 else "days"))
        if hours > 0:
            string_pieces.append('{} {}'.format(hours, "hour" if hours == 1 else "hours"))
        if minutes > 0:
            string_pieces.append('{} {}'.format(minutes, "minute" if minutes == 1 else "minutes"))
        # Something should be always written
        if seconds > 0 or not string_pieces:
            string_pieces.append('{} {}'.format(seconds, "second" if seconds == 1 else "seconds"))
        time_str = ", ".join(string_pieces[:2]) + " ago"# only the two most significant pieces 
            

    cid = str(c.pk).ljust(8)
    cstate = str(c.get_state()).ljust(20)
    jstate = str(c.get_scheduler_state()).ljust(20) if c.get_scheduler_state() is not None else "***".ljust(20)
    jid = str(c.get_job_id()).ljust(10) if c.get_job_id() is not None else "***".ljust(10)

    print cid, cstate, jstate, jid, time_str




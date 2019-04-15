# -*- coding: utf-8 -*-

import datetime
# XXX to remove when we implements the settings/tasks using SQLA
from dateutil.parser import parse

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from aiida.common.datastructures import sort_states, calc_states
from aiida.common.exceptions import ModificationNotAllowed, DbContentError
from aiida.common.utils import str_timedelta

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.utils import get_automatic_user
from aiida.backends.sqlalchemy.models.calcstate import DbCalcState
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.backends.sqlalchemy.models.group import DbGroup

from aiida.orm.implementation.sqlalchemy.utils import django_filter
from aiida.orm.implementation.sqlalchemy.calculation import Calculation
from aiida.orm.implementation.general.calculation.job import AbstractJobCalculation
from aiida.orm.implementation.general.calculation import from_type_to_pluginclassname
from aiida.orm.group import Group

from aiida.utils import timezone

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class JobCalculation(AbstractJobCalculation, Calculation):

    def _set_state(self, state):
        """
        Set the state of the calculation.

        Set it in the DbCalcState to have also the uniqueness check.
        Moreover (except for the IMPORTED state) also store in the 'state'
        attribute, useful to know it also after importing, and for faster
        querying.

        .. todo:: Add further checks to enforce that the states are set
           in order?

        :param state: a string with the state. This must be a valid string,
          from ``aiida.common.datastructures.calc_states``.
        :raise: ModificationNotAllowed if the given state was already set.
        """

        if self._to_be_stored:
            raise ModificationNotAllowed("Cannot set the calculation state "
                                         "before storing")

        if state not in calc_states:
            raise ValueError(
                "'{}' is not a valid calculation status".format(state))

        old_state = self.get_state()
        if old_state:
            state_sequence = [state, old_state]

            # sort from new to old: if they are equal, then it is a valid
            # advance in state (otherwise, we are going backwards...)
            if sort_states(state_sequence) != state_sequence:
                raise ModificationNotAllowed("Cannot change the state from {} "
                                             "to {}".format(old_state, state))

        try:
            new_state = DbCalcState(dbnode=self.dbnode, state=state).save()
        except SQLAlchemyError:
            self.dbnode.session.rollback()
            raise ModificationNotAllowed("Calculation pk= {} already transited through "
                                         "the state {}".format(self.pk, state))

        # For non-imported states, also set in the attribute (so that, if we
        # export, we can still see the original state the calculation had.
        if state != calc_states.IMPORTED:
            self._set_attr('state', state)

    def get_state(self, from_attribute=False):
        """
        Get the state of the calculation.

        .. note:: this method returns the NOTFOUND state if no state
          is found in the DB.

        .. note:: the 'most recent' state is obtained using the logic in the
          ``aiida.common.datastructures.sort_states`` function.

        .. todo:: Understand if the state returned when no state entry is found
          in the DB is the best choice.

        :param from_attribute: if set to True, read it from the attributes
          (the attribute is also set with set_state, unless the state is set
          to IMPORTED; in this way we can also see the state before storing).

        :return: a string. If from_attribute is True and no attribute is found,
          return None. If from_attribute is False and no entry is found in the
          DB, return the "NOTFOUND" state.
        """
        if from_attribute:
            return self.get_attr('state', None)
        else:
            if self._to_be_stored:
                return calc_states.NEW
            else:
                this_calc_states = [c.state.code for c in DbCalcState.query.filter_by(
                    dbnode=self.dbnode).with_entities(DbCalcState.state)]
                if not this_calc_states:
                    return None
                else:
                    try:
                        most_recent_state = sort_states(this_calc_states)[0]
                    except ValueError as e:
                        raise DbContentError("Error in the content of the "
                                             "DbCalcState table ({})".format(e.message))

                    return most_recent_state

    @classmethod
    def _list_calculations(cls, states=None, past_days=None, group=None,
                           group_pk=None, all_users=False, pks=[],
                           relative_ctime=True):
        """
        Return a string with a description of the AiiDA calculations.

        .. todo:: does not support the query for the IMPORTED state (since it
          checks the state in the Attributes, not in the DbCalcState table).
          Decide which is the correct logi and implement the correct query.

        :param states: a list of string with states. If set, print only the
            calculations in the states "states", otherwise shows all.
            Default = None.
        :param past_days: If specified, show only calculations that were
            created in the given number of past days.
        :param group: If specified, show only calculations belonging to a
            user-defined group with the given name.
            Can use colons to separate the group name from the type,
            as specified in :py:meth:`aiida.orm.group.Group.get_from_string`
            method.
        :param group_pk: If specified, show only calculations belonging to a
            user-defined group with the given PK.
        :param pks: if specified, must be a list of integers, and only
            calculations within that list are shown. Otherwise, all
            calculations are shown.
            If specified, sets state to None and ignores the
            value of the ``past_days`` option.")
        :param relative_ctime: if true, prints the creation time relative from now.
                               (like 2days ago). Default = True
        :param all_users: if True, list calculation belonging to all users.
                           Default = False

        :return: a string with description of calculations.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.

        if states:
            for state in states:
                if state not in calc_states:
                    return "Invalid state provided: {}.".format(state)

        warnings_list = []

        now = timezone.now()

        filters = {}

        if pks:
            filters["id__in"] = pks
        else:
            if group:
                filters["dbgroups__id__in"] = g_pk
            if group_pk:
                filters["dbgroups__id"] = group_pk
            if not all_users:
                filters["user"] = get_automatic_user()
            if past_days is not None:
                now = timezone.now()
                n_days_ago = now - datetime.timedelta(days=past_days)
                filters["ctime__gte"] = n_days_ago
            if states is not None:
                filters['dbattributes']['state'] = states

        q = cls.query(**filters)


        calc_list = q.distinct().order_by('ctime').options(
            joinedload('dbcomputer').subqueryload('authinfos')
        ).all()


        ## Get the last daemon check
        try:
            # last_daemon_check = get_last_daemon_timestamp('updater', when='stop')
            # XXX place holder until we can access the settings from SQLA
            last_daemon_check = parse('2015-10-16 14:16:11.454866+02')
        except ValueError:
            last_check_string = ("# Last daemon state_updater check: "
                                 "(Error while retrieving the information)")
        else:
            if last_daemon_check is None:
                last_check_string = "# Last daemon state_updater check: (Never)"
            else:
                last_check_string = ("# Last daemon state_updater check: "
                                     "{} ({})".format(
                    str_timedelta(now - last_daemon_check, negative_to_zero=True),
                    timezone.localtime(last_daemon_check).strftime("at %H:%M:%S on %Y-%m-%d")))

        disabled_ignorant_states = [
            None, calc_states.FINISHED, calc_states.SUBMISSIONFAILED,
            calc_states.RETRIEVALFAILED, calc_states.PARSINGFAILED,
            calc_states.FAILED
        ]

        if not calc_list:
            return last_check_string

        # Variable to print latter on
        res_str_list = [last_check_string]
        str_matrix = []
        title = ['# Pk', 'State', 'Creation',
                    'Sched. state', 'Computer', 'Type']
        str_matrix.append(title)
        len_title = [len(i) for i in title]

        for calc in calc_list:
            remote_state = "None"

            state = calc._get_state_string()
            remote_computer = calc.dbnode.dbcomputer.name
            scheduler_state = calc.dbnode.attributes.get("scheduler_state", None)

            if scheduler_state is None:
                remote_state = '(unknown)'
            else:
                remote_state = str(scheduler_state)
                if scheduler_state == calc_states.WITHSCHEDULER:
                    last_check = calc.dbnode.attributes.get("scheduler_lastchecktime", None)

                    when_string, verb_string = "", ""
                    if last_check is not None:
                        when_string = " {}".format(str_timedelta(
                            now - last_check, short=True,
                            negative_to_zero=True)
                        )
                        verb_string = "was "

                    remote_state = "{}{}{}".format(verb_string, sched_state,
                                                   when_string)
            # On the Django version, there is a try/except for a ValueError. I
            # don't what call can raise it, since every call to `get` has an
            # associated default value.

            calc_module = (from_type_to_pluginclassname(calc.dbnode.type)
                            .rsplit(".", 1)[0])

            prefix = 'calculation.job'
            prefix_len = len(prefix)
            if calc_module.startswith(prefix):
                calc_module = calc_module[prefix_len:].strip()

            if relative_ctime:
                calc_ctime = str_timedelta(now - calc.dbnode.ctime,
                                           negative_to_zero=True,
                                           max_num_fields=1)
            else:
                calc_ctime = " ".join(
                    [timezone.localtime(calc.dbnode.ctime).isoformat().split('T')[0],
                     timezone.localtime(calc.dbnode.ctime).isoformat().split('T')[1]
                     .split('.')[0].rsplit(":", 1)[0]])

            # Get the auth info of the computer corresponding to the
            # calculation user
            users = filter(lambda a: a.aiidauser_id == calc.dbnode.user_id,
                           calc.dbnode.dbcomputer.authinfos)
            user_enabled = users[0].enabled if users else True

            global_enabled = calc.dbnode.dbcomputer.enabled

            enabled = " [Disabled]"
            if (user_enabled and global_enabled or
                state in disabled_ignorant_states):

                enabled = ""

            str_matrix.append([
                calc.dbnode.id,
                state,
                calc_ctime,
                remote_state,
                remote_computer + "{}".format(enabled),
                calc_module
            ])

        # prepare a formatted text of minimal row length (to fit in terminals!)
        rows = []
        for j in range(len(str_matrix[0])):
            rows.append([len(str(i[j])) for i in str_matrix])
        line_lengths = [str(max(max(rows[i]), len_title[i])) for i in range(len(rows))]
        fmt_string = "{:<" + "}|{:<".join(line_lengths) + "}"
        for row in str_matrix:
            res_str_list.append(fmt_string.format(*[str(i) for i in row]))

        res_str_list += ["# {}".format(_) for _ in warnings_list]
        return "\n".join(res_str_list)

# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import datetime
from django.db import transaction, IntegrityError
from django.db.models import Q
from aiida.common.utils import str_timedelta
from aiida.common.datastructures import sort_states, calc_states
from aiida.common.exceptions import ModificationNotAllowed, DbContentError
from aiida.backends.djsite.utils import get_automatic_user
from aiida.orm.group import Group
from aiida.orm.implementation.django.calculation import Calculation
from aiida.orm.implementation.general.calculation.job import (
    AbstractJobCalculation)
from aiida.common.old_pluginloader import from_type_to_pluginclassname
from aiida.utils import timezone



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

        from aiida.common.datastructures import sort_states
        from aiida.backends.djsite.db.models import DbCalcState

        if not self.is_stored:
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
            with transaction.atomic():
                new_state = DbCalcState(dbnode=self.dbnode, state=state).save()
        except IntegrityError:
            raise ModificationNotAllowed(
                "Calculation pk= {} already transited through "
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
        from aiida.backends.djsite.db.models import DbCalcState
        if from_attribute:
            return self.get_attr('state', None)
        else:
            if not self.is_stored:
                return calc_states.NEW
            else:
                this_calc_states = DbCalcState.objects.filter(
                    dbnode=self).values_list('state', flat=True)
                if not this_calc_states:
                    return None
                else:
                    try:
                        most_recent_state = sort_states(this_calc_states)[0]
                    except ValueError as e:
                        raise DbContentError("Error in the content of the "
                                             "DbCalcState table ({})".format(
                            e.message))

                    return most_recent_state

    @classmethod
    def _list_calculations_old(cls, states=None, past_days=None, group=None,
                               group_pk=None, all_users=False, pks=[],
                               relative_ctime=True):
        """
        Return a string with a description of the AiiDA calculations.

        .. todo:: does not support the query for the IMPORTED state (since it
          checks the state in the Attributes, not in the DbCalcState table).
          Decide which is the correct logic and implement the correct query.

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
        from aiida.backends.djsite.db.models import DbAuthInfo, DbAttribute
        from aiida.daemon.timestamps import get_last_daemon_timestamp

        if states:
            for state in states:
                if state not in calc_states:
                    return "Invalid state provided: {}.".format(state)

        warnings_list = []

        now = timezone.now()

        if pks:
            q_object = Q(pk__in=pks)
        else:
            q_object = Q()

            if group is not None:
                g_pk = Group.get_from_string(group).pk
                q_object.add(Q(dbgroups__pk=g_pk), Q.AND)

            if group_pk is not None:
                q_object.add(Q(dbgroups__pk=group_pk), Q.AND)

            if not all_users:
                q_object.add(Q(user=get_automatic_user()), Q.AND)

            if states is not None:
                q_object.add(Q(dbattributes__key='state',
                               dbattributes__tval__in=states, ), Q.AND)
            if past_days is not None:
                now = timezone.now()
                n_days_ago = now - datetime.timedelta(days=past_days)
                q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

        calc_list_pk = list(
            cls.query(q_object).distinct().values_list('pk', flat=True))

        calc_list = cls.query(pk__in=calc_list_pk).order_by('ctime')

        scheduler_states = dict(
            DbAttribute.objects.filter(dbnode__pk__in=calc_list_pk,
                                       key='scheduler_state').values_list(
                'dbnode__pk', 'tval'))

        # I do the query now, so that the list of pks gets cached
        calc_list_data = list(
            calc_list.filter(
                # dbcomputer__dbauthinfo__aiidauser=F('user')
            ).distinct().order_by('ctime').values(
                'pk', 'dbcomputer__name', 'ctime',
                'type', 'dbcomputer__enabled',
                'dbcomputer__pk',
                'user__pk'))
        list_comp_pk = [i['dbcomputer__pk'] for i in calc_list_data]
        list_aiduser_pk = [i['user__pk']
                           for i in calc_list_data]
        enabled_data = DbAuthInfo.objects.filter(
            dbcomputer__pk__in=list_comp_pk, aiidauser__pk__in=list_aiduser_pk
        ).values_list('dbcomputer__pk', 'aiidauser__pk', 'enabled')

        enabled_auth_dict = {(i[0], i[1]): i[2] for i in enabled_data}

        states = {c.pk: c._get_state_string() for c in calc_list}

        scheduler_lastcheck = dict(DbAttribute.objects.filter(
            dbnode__in=calc_list,
            key='scheduler_lastchecktime').values_list('dbnode__pk', 'dval'))

        ## Get the last daemon check
        try:
            last_daemon_check = get_last_daemon_timestamp('updater',
                                                          when='stop')
        except ValueError:
            last_check_string = ("# Last daemon state_updater check: "
                                 "(Error while retrieving the information)")
        else:
            if last_daemon_check is None:
                last_check_string = "# Last daemon state_updater check: (Never)"
            else:
                last_check_string = ("# Last daemon state_updater check: "
                                     "{} ({})".format(
                    str_timedelta(now - last_daemon_check,
                                  negative_to_zero=True),
                    timezone.localtime(last_daemon_check).strftime(
                        "at %H:%M:%S on %Y-%m-%d")))

        disabled_ignorant_states = [
            None, calc_states.FINISHED, calc_states.SUBMISSIONFAILED,
            calc_states.RETRIEVALFAILED, calc_states.PARSINGFAILED,
            calc_states.FAILED
        ]

        if not calc_list:
            return last_check_string
        else:
            # first save a matrix of results to be printed
            res_str_list = [last_check_string]
            str_matrix = []
            title = ['# Pk', 'State', 'Creation',
                     'Sched. state', 'Computer', 'Type']
            str_matrix.append(title)
            len_title = [len(i) for i in title]

            for calcdata in calc_list_data:
                remote_state = "None"

                calc_state = states[calcdata['pk']]
                remote_computer = calcdata['dbcomputer__name']
                try:
                    sched_state = scheduler_states.get(calcdata['pk'], None)
                    if sched_state is None:
                        remote_state = "(unknown)"
                    else:
                        remote_state = '{}'.format(sched_state)
                        if calc_state == calc_states.WITHSCHEDULER:
                            last_check = scheduler_lastcheck.get(calcdata['pk'],
                                                                 None)
                            if last_check is not None:
                                when_string = " {}".format(
                                    str_timedelta(now - last_check, short=True,
                                                  negative_to_zero=True))
                                verb_string = "was "
                            else:
                                when_string = ""
                                verb_string = ""
                            remote_state = "{}{}{}".format(verb_string,
                                                           sched_state,
                                                           when_string)
                except ValueError:
                    raise

                calc_module = \
                from_type_to_pluginclassname(calcdata['type']).rsplit(".", 1)[0]
                prefix = 'calculation.job.'
                prefix_len = len(prefix)
                if calc_module.startswith(prefix):
                    calc_module = calc_module[prefix_len:].strip()

                if relative_ctime:
                    calc_ctime = str_timedelta(now - calcdata['ctime'],
                                               negative_to_zero=True,
                                               max_num_fields=1)
                else:
                    calc_ctime = " ".join([timezone.localtime(
                        calcdata['ctime']).isoformat().split('T')[0],
                                           timezone.localtime(calcdata[
                                                                  'ctime']).isoformat().split(
                                               'T')[1].split('.')[
                                               0].rsplit(":", 1)[0]])

                the_state = states[calcdata['pk']]

                # decide if it is needed to print enabled/disabled information
                # By default, if the computer is not configured for the
                # given user, assume it is user_enabled
                user_enabled = enabled_auth_dict.get(
                    (calcdata['dbcomputer__pk'],
                     calcdata['user__pk']), True)
                global_enabled = calcdata["dbcomputer__enabled"]

                enabled = "" if (user_enabled and global_enabled or
                                 the_state in disabled_ignorant_states) else " [Disabled]"

                str_matrix.append([calcdata['pk'],
                                   the_state,
                                   calc_ctime,
                                   remote_state,
                                   remote_computer + "{}".format(enabled),
                                   calc_module
                                   ])

            # prepare a formatted text of minimal row length (to fit in terminals!)
            rows = []
            for j in range(len(str_matrix[0])):
                rows.append([len(str(i[j])) for i in str_matrix])
            line_lengths = [str(max(max(rows[i]), len_title[i])) for i in
                            range(len(rows))]
            fmt_string = "{:<" + "}|{:<".join(line_lengths) + "}"
            for row in str_matrix:
                res_str_list.append(fmt_string.format(*[str(i) for i in row]))

            res_str_list += ["# {}".format(_) for _ in warnings_list]
            return "\n".join(res_str_list)

# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
import datetime
from django.db import transaction, IntegrityError
from django.db.models import Q
from aiida.common.utils import str_timedelta
from aiida.common.datastructures import sort_states, calc_states
from aiida.common.exceptions import ModificationNotAllowed, DbContentError
from aiida.orm.group import Group
from aiida.orm.implementation.django.calculation import Calculation
from aiida.orm.implementation.general.calculation.job import AbstractJobCalculation
from aiida.plugins.loader import get_plugin_type_from_type_string
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
        super(JobCalculation, self)._set_state(state)

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
                    except ValueError as exc:
                        raise DbContentError("Error in the content of the "
                                             "DbCalcState table ({})".format(exc))

                    return most_recent_state

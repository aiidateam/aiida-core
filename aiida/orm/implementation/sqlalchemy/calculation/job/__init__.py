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
# XXX to remove when we implements the settings/tasks using SQLA
from dateutil.parser import parse

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from aiida.common.datastructures import sort_states, calc_states
from aiida.common.exceptions import ModificationNotAllowed, DbContentError
from aiida.common.utils import str_timedelta

from aiida.backends import sqlalchemy as sa
from aiida.backends.sqlalchemy.utils import get_automatic_user
from aiida.backends.sqlalchemy.models.node import DbNode, DbCalcState
from aiida.backends.sqlalchemy.models.group import DbGroup

from aiida.orm.implementation.sqlalchemy.utils import django_filter
from aiida.orm.implementation.sqlalchemy.calculation import Calculation
from aiida.orm.implementation.general.calculation.job import AbstractJobCalculation
    
from aiida.orm.group import Group

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

        .. note:: this method returns the None if no state is found


        :param from_attribute: if set to True, read it from the attributes
          (the attribute is also set with set_state, unless the state is set
          to IMPORTED; in this way we can also see the state before storing).

        :return: a string, if a state is found or *None*
        """
        if from_attribute:
            state_to_return = self.get_attr('state', None)
        else:
            if self._to_be_stored:
                state_to_return = calc_states.NEW
            else:
                # In the sqlalchemy model, the state
                most_recent_state = self.dbnode.state
                if most_recent_state:
                    state_to_return = most_recent_state.value
                else:
                    state_to_return = None
        return state_to_return


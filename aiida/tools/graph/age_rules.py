# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AGE rules"""

from __future__ import absolute_import
from __future__ import print_function

from abc import ABCMeta, abstractmethod
from enum import Enum
import six
import numpy as np

from aiida.common.exceptions import InputValidationError
from aiida.orm.querybuilder import QueryBuilder
from aiida.tools.graph.age_entities import Basket


class MODES(Enum):
    APPEND = 1
    REPLACE = 2


def check_if_basket(entity_set):
    if not isinstance(entity_set, Basket):
        raise TypeError('You need to set the walkers with an AiidaEntitySet')


@six.add_metaclass(ABCMeta)
class Operation(object):
    """Operation metaclass"""

    def __init__(self, mode, max_iterations, track_edges, track_visits):
        assert mode in MODES, 'You have to pass an option of {}'.format(MODES)
        self._mode = mode
        self.set_max_iterations(max_iterations)
        self._track_edges = track_edges  # Logical
        self._track_visits = track_visits  # Logical
        self._walkers = None
        self._visits = None
        self._iterations_done = None

    def _init_run(self, entity_set):
        pass

    def set_max_iterations(self, max_iterations):
        """Set max iterations"""
        if max_iterations is np.inf:
            pass
        elif not isinstance(max_iterations, int):
            raise TypeError('max iterations has to be an integer')
        self._maxiter = max_iterations

    def set_walkers(self, walkers):
        check_if_basket(walkers)
        self._walkers = walkers

    def get_iterations_done(self):
        return self._iterations_done

    def get_walkers(self):
        return self._walkers  #.copy(with_data=True)

    def set_visits(self, entity_set):
        check_if_basket(entity_set)
        self._visits = entity_set

    def get_visits(self):
        return self._visits

    @abstractmethod
    def _load_results(self, target_set, operational_set):
        pass

    def run(self, walkers=None, visits=None, iterations=None):
        """run method"""

        if walkers is not None:
            self.set_walkers(walkers)
        else:
            if self._walkers is None:
                raise RuntimeError('Walkers have not been set for this instance')

        if visits is not None:
            self.set_visits(visits)

        if self._track_visits and self._visits is None:
            #raise RuntimeError("Supposed to track visits, but visits have not been "
            #        "set for this instance")
            # If nothing is set, I do it here!
            self.set_visits(self._walkers.copy())

        if iterations is not None:
            self.set_max_iterations(iterations)

        self._init_run(self._walkers)
        # The active walkers are all workers where this rule-instance have
        # not been applied, yet
        active_walkers = self._walkers.copy()
        # The new_set is where I can put the results of the query
        # It starts empty.
        new_results = self._walkers.copy(with_data=False)
        # I also need somewhere to store everything I've walked to
        # with_data is set to True, since the active walkers are of course being visited
        # even before we start the iterations!
        visited_this_rule = self._walkers.copy(with_data=True)  # w
        iterations = 0
        while (active_walkers and iterations < self._maxiter):
            iterations += 1
            # loading results into new_results set:
            self._load_results(new_results, active_walkers)
            # It depends on the mode, how I update the walkers
            # I set the active walkers to all results that have not been visited yet.
            active_walkers = new_results - visited_this_rule
            # The visited is augmented:
            visited_this_rule += active_walkers

        self._iterations_done = iterations
        if self._mode == MODES.APPEND:
            self._walkers += visited_this_rule
        elif self._mode == MODES.REPLACE:
            self._walkers = active_walkers

        if self._track_visits:
            self._visits += visited_this_rule
        return self._walkers


class UpdateRule(Operation):
    """Update Rule"""

    def __init__(self, querybuilder, mode=MODES.APPEND, max_iterations=1, track_edges=False, track_visits=True):

        def get_spec_from_path(queryhelp, idx):
            if (
                queryhelp['path'][idx]['entity_type'].startswith('node') or
                queryhelp['path'][idx]['entity_type'].startswith('data') or
                queryhelp['path'][idx]['entity_type'].startswith('process') or
                queryhelp['path'][idx]['entity_type'] == ''
            ):
                result = 'nodes'
            elif queryhelp['path'][idx]['entity_type'] == 'group':
                result = 'groups'
            else:
                raise Exception('not understood entity from ( {} )'.format(queryhelp['path'][idx]['entity_type']))
            return result

        queryhelp = querybuilder.queryhelp
        #print('\n\nDICT:')
        #import pprint
        #pprint.pprint(queryhelp)
        #print('---\n')
        for pathspec in queryhelp['path']:
            if not pathspec['entity_type']:
                pathspec['entity_type'] = 'node.Node.'
        self._querybuilder = QueryBuilder(**queryhelp)
        queryhelp = self._querybuilder.queryhelp
        self._first_tag = queryhelp['path'][0]['tag']
        self._last_tag = queryhelp['path'][-1]['tag']

        # All of these are set in _init_run:
        self._edge_label = None
        self._edge_keys = None
        self._entity_to_identifier = None

        self._entity_from = get_spec_from_path(queryhelp, 0)
        self._entity_to = get_spec_from_path(queryhelp, -1)
        super(UpdateRule, self).__init__(mode, max_iterations, track_edges=track_edges, track_visits=track_visits)

    def _init_run(self, entity_set):
        # pylint: disable=protected-access

        # Removing all other projections in the QueryBuilder instance:
        for tag in self._querybuilder._projections:
            self._querybuilder._projections[tag] = []

        # priming querybuilder to add projection on the key I need:
        self._querybuilder.add_projection(self._last_tag, entity_set[self._entity_to].identifier)
        self._entity_to_identifier = entity_set[self._entity_to].identifier
        if self._track_edges:
            self._querybuilder.add_projection(self._first_tag, entity_set[self._entity_to].identifier)
            edge_set = entity_set.dict['{}_{}'.format(self._entity_from, self._entity_to)]
            self._edge_label = '{}--{}'.format(self._first_tag, self._last_tag)
            self._edge_keys = tuple([(self._first_tag, entity_set[self._entity_from].identifier),
                                     (self._last_tag, entity_set[self._entity_to].identifier)] +
                                    [(self._edge_label, identifier)
                                     for identifier in edge_set.get_additional_identifiers()])
            try:
                self._querybuilder.add_projection(self._edge_label, edge_set.get_additional_identifiers())
            except InputValidationError:
                raise KeyError(
                    'The key for the edge is invalid.\n'
                    'Are the entities really connected, or have you overwritten the edge-tag?'
                )

    def _load_results(self, target_set, operational_set):
        """
        :param target_set: The set to load the results into
        :param operational_set: Where the results originate from (walkers)
        """
        # I check that I have primary keys
        primkeys = operational_set[self._entity_from].get_keys()
        # Empty the target set, so that only these results are inside
        target_set.empty()
        if primkeys:
            self._querybuilder.add_filter(
                self._first_tag, {operational_set[self._entity_from].identifier: {
                                      'in': primkeys
                                  }}
            )
            qres = self._querybuilder.dict()
            # These are the new results returned by the query
            target_set[self._entity_to].add_entities([
                item[self._last_tag][self._entity_to_identifier] for item in qres
            ])
            if self._track_edges:
                target_set['{}_{}'.format(self._entity_to, self._entity_to)].add_entities([
                    tuple(item[key1][key2] for (key1, key2) in self._edge_keys) for item in qres
                ])
        # Everything is changed in place, no need to return anything


class RuleSaveWalkers(Operation):
    """Rule Save Walkers"""

    def __init__(self, stash):
        self._stash = stash
        super(RuleSaveWalkers, self).__init__(mode=MODES.REPLACE, max_iterations=1, track_edges=True, track_visits=True)

    def _load_results(self, target_set, operational_set):
        self._stash += self._walkers


class RuleSetWalkers(Operation):
    """Rule Set Walkers"""

    def __init__(self, stash):
        self._stash = stash
        super(RuleSetWalkers, self).__init__(mode=MODES.REPLACE, max_iterations=1, track_edges=True, track_visits=True)

    def _load_results(self, target_set, operational_set):
        self._walkers.empty()
        self._walkers += self._stash


class RuleSequence(Operation):
    """Rule Sequence"""

    def __init__(self, rules, mode=MODES.APPEND, max_iterations=1, track_edges=False, track_visits=True):
        for rule in rules:
            if not isinstance(rule, Operation):
                print(rule)
                raise TypeError('rule has to be an instance of Operation-subclass')
        self._rules = rules
        super(RuleSequence, self).__init__(mode, max_iterations, track_edges=track_edges, track_visits=track_visits)

    def _load_results(self, target_set, operational_set):  #ex: active_walkers as last arg
        target_set.empty()
        for _, rule in enumerate(self._rules):
            # I iterate the operational_set through all the rules:
            #rule.set_walkers(active_walkers)
            rule.set_visits(self._visits)
            rule.set_walkers(self._walkers)
            target_set += rule.run()

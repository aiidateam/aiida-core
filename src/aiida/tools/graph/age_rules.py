###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Rules for the AiiDA Graph Explorer utility"""

from abc import ABCMeta, abstractmethod
from collections import defaultdict
from copy import deepcopy

import numpy as np

from aiida import orm
from aiida.common.datastructures import DEFAULT_FILTER_SIZE
from aiida.common.lang import type_check
from aiida.tools.graph.age_entities import Basket


class Operation(metaclass=ABCMeta):
    """Base class for all AGE explorer classes"""

    def __init__(self, max_iterations, track_edges):
        """Initialization method

        :param max_iterations: maximum number of iterations to perform.
        :param bool track_edges: if True, will also track and return the edges traversed.
        """
        self.set_max_iterations(max_iterations)
        self._track_edges = track_edges
        self._iterations_done = None

    def set_max_iterations(self, max_iterations):
        """Sets the max iterations"""
        if not (isinstance(max_iterations, int) or max_iterations is np.inf):
            raise TypeError('max_iterations has to be an integer or np.inf')
        self._max_iterations = max_iterations

    @property
    def iterations_done(self):
        """Number of iterations performed"""
        return self._iterations_done

    @abstractmethod
    def run(self, operational_set):
        """Takes the operational_set and overwrites it with the set of nodes that results
        from applying the rule (this might or not include the initial set of nodes as
        well depending on the rule).

        :type operational_set: :py:class:`aiida.tools.graph.age_entities.Basket`
        :param operational_set: initital set of nodes to be overwritten by the rule.
        """


class QueryRule(Operation, metaclass=ABCMeta):
    """Parent class for every rule that implements a query.

    QueryRules take a generic QueryBuilder instance and a set of starting nodes and then
    perform successive iterations of that query, each one from the set of nodes that the
    previous one found. Depending on the class of rule used the final result will be
    either the whole set of nodes traversed (UpdateRule), or only the final set of nodes
    found in the last iteration of the query (ReplaceRule).
    """

    def __init__(self, querybuilder: orm.QueryBuilder, max_iterations=1, track_edges=False):
        """Initialization method

        :param querybuilder: an instance of the QueryBuilder class from which to take the
            procedure for traversal
        :param int max_iterations: the number of iterations to run this query on (must be
            a finite number for ReplaceRules)
        :param bool track_edges: whether to track which edges are traversed and store them
        """
        super().__init__(max_iterations, track_edges=track_edges)

        def get_spec_from_path(query_dict, idx):
            from aiida.orm.querybuilder import GROUP_ENTITY_TYPE_PREFIX

            if (
                query_dict['path'][idx]['entity_type'].startswith('node')
                or query_dict['path'][idx]['entity_type'].startswith('data')
                or query_dict['path'][idx]['entity_type'].startswith('process')
                or query_dict['path'][idx]['entity_type'] == ''
            ):
                result = 'nodes'
            elif query_dict['path'][idx]['entity_type'].startswith(GROUP_ENTITY_TYPE_PREFIX):
                result = 'groups'
            else:
                raise RuntimeError(f'not understood entity from ( {query_dict["path"][idx]["entity_type"]} )')
            return result

        query_dict = querybuilder.as_dict()

        # Check if there is any projection:
        query_projections = query_dict['project']
        for projection_key in query_projections:
            if query_projections[projection_key] != []:
                raise ValueError(
                    'The input querybuilder must not have any projections.\n'
                    'Instead, it has the following:\n - Key: {}\n - Val: {}\n'.format(
                        projection_key, query_projections[projection_key]
                    )
                )
        for pathspec in query_dict['path']:
            if not pathspec['entity_type']:
                pathspec['entity_type'] = 'node.Node.'
        self._qbtemplate = deepcopy(querybuilder)
        query_dict = self._qbtemplate.as_dict()
        self._first_tag = query_dict['path'][0]['tag']
        self._last_tag = query_dict['path'][-1]['tag']
        self._querybuilder = None

        # All of these are set in _init_run:
        self._edge_label = None
        self._edge_keys = None
        self._entity_to_identifier = None

        self._entity_from = get_spec_from_path(query_dict, 0)
        self._entity_to = get_spec_from_path(query_dict, -1)
        self._accumulator_set = None

    def set_edge_keys(self, edge_keys):
        """Set the edge keys that are use to classify the edges during the run of this query.

        :param edge_keys:
            a list of projections on the edge itself, or a tuple that specifies
            (tag, project) if the projection is not on the edge

        Example: For node-to-node graph traversals, it is often convenient to save
        the information on the links::

            qb  = QueryBuilder().append(Node, tag='n1').append(Node, tag='n2')
            rule = RuleSequence(qb, track_edges=True)
            rule.set_edge_keys(['input_id', 'output_id', 'label', 'type'])

            # Now for UUIDS:
            qb  = QueryBuilder().append(Node, tag='n1').append(Node, tag='n2')
            rule = RuleSequence(qb, track_edges=True)
            rule.set_edge_keys([('n1','uuid'), ('n2','uuid'), 'label', 'type'])
        """
        self._edge_keys = edge_keys[:]

    def _init_run(self, operational_set):
        """Initialization Utility method

        This method initializes a run. It initializes the accumulator_set in order
        for it to only contain the operational_set, and to be of the same kind.
        This function modifies the its QueryBuilder instance to give the right results.

        :param operational_set: input with which to initialize the accumulator_set.
        """
        type_check(operational_set, Basket)
        if self._accumulator_set is not None:
            type_check(self._accumulator_set, Basket)
            self._accumulator_set.empty()
            self._accumulator_set += operational_set
        else:
            self._accumulator_set = operational_set.copy()

        # Copying qbtemplate so there's no problem if it is used again in a later run:
        query_dict = self._qbtemplate.as_dict()
        self._querybuilder = deepcopy(self._qbtemplate)

        self._entity_to_identifier = operational_set[self._entity_to].identifier

        # Now I add the necessary projections, which is the identifier of the
        # last entity of the QueryBuilder path:
        self._querybuilder.add_projection(self._last_tag, self._entity_to_identifier)

        if self._track_edges:
            # This requires additional projections and the edge_keys, which is a list of tuples (of length 2)
            # that stores the information what I need to project as well, as in (tag, projection)
            projections = defaultdict(list)
            self._edge_keys = []
            self._edge_label = query_dict['path'][-1]['edge_tag']

            # Need to get the edge_set: This is given by entity1_entity2. Here, the results needs to
            # be sorted somehow in order to ensure that the same key is used when entity_from and
            # entity_to are exchanged.
            edge_set = operational_set.dict['{}_{}'.format(*sorted((self._entity_from, self._entity_to)))]

            # Looping over the edge identifiers to figure out what I need to project and in which
            # order. The order is important! The rules:
            # r1 = Rule(QueryBuilder().append(Group).append(Node, with_group=Group) and
            # r2 = Rule(QueryBuilder().append(Node).append(Group, with_node=Node)
            # need still to save their results in the same order (i.e. group_id, node_id).
            # Therefore, I am sorting the edge_keys according to edge_identifiers specified in the edge_set
            for tag, projection in edge_set.edge_identifiers:
                if tag == 'edge':
                    actual_tag = self._edge_label
                elif tag == self._entity_from:
                    actual_tag = self._first_tag
                elif tag == self._entity_to:
                    actual_tag = self._last_tag
                else:
                    # For now I can only specify edge_identifiers as 'edge', ie. project on the edge
                    # itself, or by the entity_from, entity_to keyword, ie. groups or nodes.
                    # One could think of other keywords...
                    raise ValueError(f'This tag ({tag}) is not known')
                self._edge_keys.append((actual_tag, projection))
                projections[actual_tag].append(projection)

            # Telling the QB about the additional projections:
            for proj_tag, projectionlist in projections.items():
                try:
                    self._querybuilder.add_projection(proj_tag, projectionlist)
                except (TypeError, ValueError) as exc:
                    raise KeyError('The projection for the edge-identifier is invalid.\n') from exc

    def _load_results(self, target_set, operational_set):
        """Single application of the rules to the operational set

        :param target_set:
            where the new results will be loaded (it will be first emptied of all previous content).
            There is no returned value for this method.
        :param operational_set: where the results originate from (walkers)
        """
        from aiida.common.utils import batch_iter

        primkeys = operational_set[self._entity_from].keyset
        target_set.empty()

        if not primkeys:
            return

        # Batch the queries for large datasets using batch_iter
        all_results = []

        for _, batch_primkeys in batch_iter(iterable=primkeys, size=DEFAULT_FILTER_SIZE):
            batch_qb = deepcopy(self._querybuilder)
            batch_qb.add_filter(
                self._first_tag, {operational_set[self._entity_from].identifier: {'in': batch_primkeys}}
            )
            all_results.extend(batch_qb.dict())

        # These are the new results returned by the query
        target_set[self._entity_to].add_entities(
            [item[self._last_tag][self._entity_to_identifier] for item in all_results]
        )

        if self._track_edges:
            # As in _init_run, I need the key for the edge_set
            edge_key = '{}_{}'.format(*sorted((self._entity_from, self._entity_to)))
            edge_set = operational_set.dict[edge_key]
            namedtuple_ = edge_set.edge_namedtuple

            target_set[edge_key].add_entities(
                [namedtuple_(*(item[key1][key2] for (key1, key2) in self._edge_keys)) for item in all_results]
            )

    def set_accumulator(self, accumulator_set):
        self._accumulator_set = accumulator_set

    def empty_accumulator(self):
        if self._accumulator_set is not None:
            self._accumulator_set.empty()

    # Pylint complains if this is not here, but should be removed asap
    def run(self, operational_set):
        pass


class UpdateRule(QueryRule):
    """The UpdateRule will accumulate every node visited and return it as a set of nodes
    (and thus, without duplication). It can be used requesting both a finite number
    of iterations or an infinite number of iterations (in which case it will stop once
    no new nodes are added to the accumulation set).
    """

    def run(self, operational_set):
        self._init_run(operational_set)
        self._iterations_done = 0
        new_results = operational_set.get_template()

        # The operational_set will be updated with the new_nodes that were not
        # already in the _acumulator_set, so that we are not querying from the
        # same nodes again and the cycle can end when no new nodes are found
        while operational_set and self._iterations_done < self._max_iterations:
            self._iterations_done += 1
            self._load_results(new_results, operational_set)
            operational_set = new_results - self._accumulator_set
            self._accumulator_set += new_results

        return self._accumulator_set.copy()


class ReplaceRule(QueryRule):
    """The ReplaceRule does not accumulate results, but just sets the operational_set to
    new results. Therefore it can only function using a finite number of iterations,
    since it does not keep track of which nodes where visited already (otherwise, if
    it was following a cycle, it would run indefinitely).
    """

    def __init__(self, querybuilder, max_iterations=1, track_edges=False):
        if max_iterations == np.inf:
            raise ValueError('You cannot have max_iterations to be infinitely large for replace rules')
        super().__init__(querybuilder, max_iterations=max_iterations, track_edges=track_edges)

    def run(self, operational_set):
        self._init_run(operational_set)
        self._iterations_done = 0
        new_results = operational_set.get_template()

        # The operational_set will be replaced by the new_nodes, even if these
        # were already visited previously.
        while operational_set and self._iterations_done < self._max_iterations:
            self._iterations_done += 1
            self._load_results(new_results, operational_set)
            operational_set = new_results

        return operational_set.copy()


class RuleSaveWalkers(Operation):
    """Save the Walkers:

    When initialized, this rule will save a pointer to an external stash variable.
    When run, this stash will be emptied and a given operational_set will be saved
    there instead.
    """

    def __init__(self, stash):
        """Initialization method

        :param stash: external variable in which to save the operational_set
        """
        self._stash = stash
        super().__init__(max_iterations=1, track_edges=True)

    def run(self, operational_set):
        self._stash.empty()
        self._stash += operational_set
        return operational_set


class RuleSetWalkers(Operation):
    """Set the Walkers:

    When initialized, this rule will save a pointer to an external stash variable.
    When run, the given operational_set will be emptied and the stash will be
    loaded in it.
    """

    def __init__(self, stash):
        """Initialization method

        :param stash: external variable from which to load into the operational_set
        """
        self._stash = stash
        super().__init__(max_iterations=1, track_edges=True)

    def run(self, operational_set):
        operational_set.empty()
        operational_set += self._stash
        return operational_set


class RuleSequence(Operation):
    """Rule for concatenation

    Rule Sequence is used to concatenate a series of rules together.
    Concatenating querybuilders in a single rule its not enough because
    one might want to stash results to perform two independent operations
    in the starting set instead of a second operation from the results of
    the first (see RuleSetWalkers and RuleSaveWalkers).
    """

    def __init__(self, rules, max_iterations=1):
        for rule in rules:
            if not isinstance(rule, Operation):
                raise TypeError('rule has to be an instance of Operation-subclass')
        self._rules = rules
        self._accumulator_set = None
        self._visits_set = None
        super().__init__(max_iterations, track_edges=False)

    def run(self, operational_set):
        type_check(operational_set, Basket)

        if self._accumulator_set is not None:
            type_check(self._accumulator_set, Basket)
            self._accumulator_set.empty()
            self._accumulator_set += operational_set
        else:
            self._accumulator_set = operational_set.copy()
        if self._visits_set is not None:
            type_check(self._visits_set, Basket)
            self._visits_set.empty()
            self._visits_set += operational_set
        else:
            self._visits_set = operational_set.copy()

        new_results = operational_set.get_template()
        self._iterations_done = 0
        while operational_set and self._iterations_done < self._max_iterations:
            self._iterations_done += 1
            new_results.empty()

            # I iterate the operational_set through all the rules:
            for _, rule in enumerate(self._rules):
                operational_set = rule.run(operational_set)
                new_results += operational_set
                self._visits_set += operational_set

            # I set the operational set to all results that have not been visited yet.
            operational_set = new_results - self._accumulator_set
            self._accumulator_set += new_results

        return self._visits_set.copy()

    def set_accumulator(self, accumulator_set):
        """Set the accumulator set"""
        self._accumulator_set = accumulator_set

    def empty_accumulator(self):
        """Empties the accumulator set"""
        if self._accumulator_set is not None:
            self._accumulator_set.empty()

    def set_visits(self, visits_set):
        """Set the visits set"""
        self._visits_set = visits_set

    def empty_visits(self):
        """Empties the visits set"""
        if self._visits_set is not None:
            self._visits_set.empty()

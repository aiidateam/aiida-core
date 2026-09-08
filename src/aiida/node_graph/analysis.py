from __future__ import annotations
import numpy as np
from typing import Any, Dict, List, Set, TYPE_CHECKING, Optional
from aiida.node_graph.link import TaskLink
from aiida.node_graph import Task
from aiida.node_graph.socket import TaskSocketNamespace
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import depth_first_order

if TYPE_CHECKING:
    from aiida.node_graph import Graph


def build_adjacency_matrix(graph: Graph):
    """
    Build a sparse adjacency matrix where entry (i, j) == 1
    if there is a link from task i to task j.
    """
    # 1) Map each task name -> integer index
    nodes = list(graph.tasks)  # or however you get the Task list
    name_to_index = {task.name: i for i, task in enumerate(nodes)}
    n = len(nodes)

    # 2) Collect edges in "row, col" format
    row = []
    col = []
    for link in graph.links:
        if (
            link.from_task.name not in name_to_index
            or link.to_task.name not in name_to_index
        ):
            continue
        i = name_to_index[link.from_task.name]
        j = name_to_index[link.to_task.name]
        row.append(i)
        col.append(j)

    # 3) Build a coo_matrix of shape (n,n) with 1’s for edges
    data = np.ones(len(row), dtype=np.int8)
    adjacency = coo_matrix((data, (row, col)), shape=(n, n))

    return adjacency, name_to_index, nodes


class GraphAnalysis:
    """
    Utility to analyze a Graph, with caching to handle large graphs:
      - get_input_links / get_output_links
      - get_direct_children / get_all_descendants
      - compare_graphs by task name
    """

    def __init__(self, graph: Graph):
        self.graph = graph

        # A simple integer to track if our analysis cache is up to date
        # We assume the Graph increments some 'graph._version' each time
        # a task or link is added/removed, etc. If you don't have that,
        # you can implement your own triggers or approach.
        self._cached_version = -1
        self._adjacency = None
        self._name_to_idx = {}
        self._tasks_list = []
        # Caches
        self._cache_input_links: Dict[str, List[str]] = {}
        self._cache_output_links: Dict[str, List[str]] = {}
        self._cache_descendants: Dict[str, Set[str]] = {}
        self._cache_zone: Dict[str, Dict[str, List[str]]] = {}

    def get_input_links(self, task: Task) -> List[TaskLink]:
        """
        Return all links leading INTO the given task (by name-based lookup).
        """
        self._ensure_cache_valid()
        return self._cache_input_links.get(task.name, [])

    def get_output_links(self, task: Task) -> List[TaskLink]:
        """
        Return all links leading OUT OF the given task (by name-based lookup).
        """
        self._ensure_cache_valid()
        return self._cache_output_links.get(task.name, [])

    def get_direct_children(self, task: Task) -> List[Task]:
        """
        Nodes that receive a link from `task`.
        """
        self._ensure_cache_valid()
        links = self._cache_output_links.get(task.name, [])
        # Each link's '.to_task' is the child
        return [lk for lk in links]

    def get_all_descendants(self, task: Task) -> list[str]:

        self._ensure_cache_valid()
        return self._cache_descendants.get(task.name, [])

    @staticmethod
    def compare_graphs(g1: Graph, g2: Graph) -> Dict[str, Any]:
        """
        Compare two NodeGraphs by NAME-based task identity. Return dict:
        {
            "added_tasks":    list of task names in g2 but not in g1
            "removed_tasks":  list of task names in g1 but not in g2
            "modified_tasks":  list of task names that appear in both but differ
        }

        "differ" = input links differ OR input socket values differ (no output check).
        """
        summary = {
            "added_tasks": [],
            "removed_tasks": [],
            "modified_tasks": [],
        }

        # Map by name
        g1_nodes_by_name = {n.name: n for n in g1.tasks}
        g2_nodes_by_name = {n.name: n for n in g2.tasks}

        set1 = set(g1_nodes_by_name.keys())
        set2 = set(g2_nodes_by_name.keys())

        # Identify added/removed
        removed = set1 - set2
        added = set2 - set1
        summary["removed_tasks"] = sorted(list(removed))
        summary["added_tasks"] = sorted(list(added))

        # For nodes present in both, check changes
        common = set1.intersection(set2)
        for nname in common:
            task1 = g1_nodes_by_name[nname]
            task2 = g2_nodes_by_name[nname]
            if GraphAnalysis._task_changed(g1, task1, g2, task2):
                summary["modified_tasks"].append(nname)

        # Sort changed nodes for consistent output
        summary["modified_tasks"].sort()
        return summary

    def build_connectivity(self):
        self._ensure_cache_valid()
        connectivity = {
            "child_node": self._cache_descendants,
            "input_node": self._cache_input_links,
            "output_node": self._cache_output_links,
            "zone": self._cache_zone,
        }
        return connectivity

    def build_zone(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Analyse *zones* (nodes that own a non-empty ``children`` list).

        For each such task we return::

            {
                zone_name: {
                    "children":     [...names inside the zone...],
                    "input_tasks":  [...external nodes feeding the zone...]
                }
            }

        *External inputs* are compressed to the **closest ancestor** outside
        the zone.
        """
        self._ensure_cache_valid()
        return self._cache_zone

    @staticmethod
    def _task_changed(g1: Graph, n1: Task, g2: Graph, n2: Task) -> bool:
        """
        Decide if n1 and n2 differ by:
          - input links
          - input socket values
        """
        if GraphAnalysis._input_links_changed(g1, n1, g2, n2):
            return True
        if GraphAnalysis._input_values_changed(n1, n2):
            return True
        return False

    @staticmethod
    def _input_links_changed(g1: Graph, n1: Task, g2: Graph, n2: Task) -> bool:
        """Compare input links (all links where .to_task == n1 vs. .to_task == n2)."""
        # We'll gather a set of (.from_task_name, from_socket_name) for each
        in_links_1 = set()
        for lk in g1.links:
            if lk.to_task == n1:
                in_links_1.add((lk.from_task.name, lk.from_socket._name))

        in_links_2 = set()
        for lk in g2.links:
            if lk.to_task == n2:
                in_links_2.add((lk.from_task.name, lk.from_socket._name))

        return in_links_1 != in_links_2

    @staticmethod
    def _input_values_changed(n1: Task, n2: Task) -> bool:
        """
        Compare only *input* socket values.
        We skip output sockets, as requested.
        """
        in1 = n1.get_input_names()
        in2 = n2.get_input_names()

        # If the sets of input socket names differ, we consider them changed
        if set(in1) != set(in2):
            return True

        # For matching input names, compare values
        for name in in1:
            if isinstance(n1.inputs[name], TaskSocketNamespace):
                continue
            v1 = n1.inputs[name].value
            v2 = n2.inputs[name].value
            if GraphAnalysis._values_different(v1, v2):
                return True
        return False

    @staticmethod
    def _values_different(v1: Any, v2: Any) -> bool:
        """
        Safe-compare that won't fail for NumPy arrays. You can expand logic
        for other special cases. If you don't use NumPy, or if your array
        type is different, adjust accordingly.
        """
        # Case 1: Different types => different
        if type(v1) != type(v2):
            return True

        # Optionally handle None vs. non-None
        if v1 is None and v2 is None:
            return False
        if (v1 is None) ^ (v2 is None):
            return True

        # If both are NumPy arrays, compare with array_equal
        if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
            return not np.array_equal(v1, v2)

        # Fallback to normal "!=" comparison
        return v1 != v2

    def _ensure_cache_valid(self):
        """
        If the graph version changed, rebuild the adjacency-based caches:
          - input_links[task.name]
          - output_links[task.name]
          - all_descendants[task.name]
        """
        current_version = getattr(self.graph, "_version", 0)
        if current_version != self._cached_version:
            self._rebuild_cache()
            self._cached_version = current_version

    def _rebuild_cache(self):
        """
        Rebuild adjacency caches for all nodes:
          self._cache_input_links[name] = [links leading into name]
          self._cache_output_links[name] = [links from name]
          self._cache_descendants[name] = set of all downstream task names
        """
        self._cache_input_links.clear()
        self._cache_output_links.clear()
        self._cache_descendants.clear()

        # Initialize empty lists for each task name
        for task in self.graph.tasks:
            self._cache_input_links[task.name] = []
            self._cache_output_links[task.name] = []

        # Populate input/output links
        for link in self.graph.links:
            from_name = link.from_task.name
            to_name = link.to_task.name
            # in case the task does not belong to the graph
            if from_name not in self.graph.tasks or to_name not in self.graph.tasks:
                continue
            self._cache_output_links[from_name].append(to_name)
            self._cache_input_links[to_name].append(from_name)

        # For descendants, do a DFS/BFS from each task
        self._adjacency, self._name_to_idx, self._tasks_list = build_adjacency_matrix(
            self.graph
        )
        for task in self.graph.tasks:
            if task.name not in self._name_to_idx:
                self._cache_descendants[task.name] = []

            idx = self._name_to_idx[task.name]
            order, _ = depth_first_order(self._adjacency, idx)
            # Filter out the starting task
            order = [x for x in order if x != idx]
            self._cache_descendants[task.name] = [
                self._tasks_list[x].name for x in order
            ]
        # Build zone cache
        self._compute_zone_cache()

    def _compute_zone_cache(self):
        """
        Populate ``_cache_zone`` for every task (each task is a "zone").


        1) **Direct child / parent mapping**
           - Build `direct_children[task]` from `task.children`.
           - Build `parent_of[child] = parent` for each child.

        2) **Parent chains**
           - `parent_chain(name)` returns a list [`parent`, ..., None]

        3) **Recursive zone input discovery** via `zone_inputs(zone_name)`:

           A) **Raw inputs**: tasks linked directly into `zone_name`.

           B) **Child zone inputs**:
              - If a child is itself a zone, recurse `zone_inputs(child)`;
                include sources that lie outside the child's direct children.
              - Otherwise, include the child's direct inputs.

           C) **Filter internal**:
              - Exclude sources whose `parent_chain` ever enters
                this zone's direct children.

           D) **Collapse to producer-zones**:
              - For each source, compute its `parent_chain`.
              - Find the first common ancestor with the current zone's chain.
              - If ancestor is itself, keep source; else pick the zone one level up.

           E) **Cache result**:
              - Store under `_cache_zone[zone_name]` with
                {
                  'children': direct children,
                  'input_tasks': sorted unique final inputs
                }.

        Finally, invoke `zone_inputs` for every task to populate the cache.
        """
        # --- 1) build child / parent mappings --------------------------------
        direct_children: Dict[str, List[str]] = {
            n.name: [
                c.name if isinstance(c, Task) else c for c in getattr(n, "children", [])
            ]
            for n in self.graph.tasks
        }
        parent_of: Dict[str, Optional[str]] = {}
        for parent, kids in direct_children.items():
            for k in kids:
                parent_of[k] = parent

        parent_chain_cache: Dict[str, List[Optional[str]]] = {}

        def parent_chain(name: str) -> List[Optional[str]]:
            if name in parent_chain_cache:
                return parent_chain_cache[name]
            parent = parent_of.get(name)
            if parent is None:
                chain = [None]
            else:
                chain = [parent] + parent_chain(parent)
            parent_chain_cache[name] = chain
            return chain

        # --- 2) recursive zone input discovery ------------------------------
        zone_cache: Dict[str, Dict[str, List[str]]] = {}

        def zone_inputs(zone_name: str) -> List[str]:
            if zone_name in zone_cache:
                return zone_cache[zone_name]["input_tasks"]

            # gather all direct children (may be empty for a leaf-zone)
            kids = direct_children[zone_name]

            # step A – raw input tasks (direct links into zone itself)
            inputs: List[str] = list(self._cache_input_links.get(zone_name, []))

            # step B – recurse into children
            for child in kids:
                if direct_children[child]:  # child is itself a zone
                    for src in zone_inputs(child):
                        if src not in kids:
                            inputs.append(src)
                else:  # child is a plain task
                    inputs.extend(self._cache_input_links.get(child, []))

            # step C – keep only tasks that are *truly outside* the zone
            new_inputs: List[str] = []
            for src in inputs:
                chain_to_check = [src] + parent_chain(src)
                if not any(t in kids for t in chain_to_check):
                    new_inputs.append(src)

            # step D – collapse each source to the correct producer-zone
            final_inputs: List[str] = []
            parents_of_zone = parent_chain(zone_name)
            for src in new_inputs:
                # first common ancestor between src-zone chain and this zone
                src_chain = parent_chain(src)
                common_parent: Optional[str] = None
                for p in parents_of_zone:
                    if p in src_chain:
                        common_parent = p
                        break
                # find index to pick correct zone level
                idx = (
                    src_chain.index(common_parent) if common_parent in src_chain else 0
                )
                chosen = src if idx == 0 else src_chain[idx - 1]
                final_inputs.append(chosen)

            final_inputs = sorted(set(final_inputs))

            zone_cache[zone_name] = {
                "children": kids,
                "input_tasks": final_inputs,
            }
            return final_inputs

        # build cache for *every* task (every task is a zone)
        for n in self.graph.tasks:
            zone_inputs(n.name)

        self._cache_zone = zone_cache

    @staticmethod
    def _to_name(obj) -> str:
        return obj if isinstance(obj, str) else obj.name

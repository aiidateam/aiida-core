#import aida.orm.node

''' 
Graph Rules:

1. Each Data node must have zero or one source calculation
2. Each calculation node must have one or more data inputs
3. Each calculation must be linked to one and only one code
4. Each calculation must be linked to one and only one computer

5. A data node may contain multiple data nodes. This is nested hierarchy. 
If there is a link between a data and a caclulation, there must be a link 
between at least one sub-data and one sub-calculation.
6. A calculation node may contain multiple calculation nodes. This is a workflow.



'''

def NodeValidity():
    '''
    Get all the nodes from DB and check their validity using internal methods.
    Return list of invalid nodes
    '''
    nodelist = Node.query()
    return [node.pk for node in nodelist if not node.validate()]


def GraphConsistency():
    '''
    itemlist = Item.query()
    '''
    if self.type == 'calculation':
        raise GraphError('Node {0} violates connection rules')



def GraphLoops(graph):
    ''' 
    Find the strongly connected components in a graph using Tarjan's algorithm.
    graph should be a dictionary mapping node names to lists of successor nodes.
    '''
        
    result = [ ]
    stack = [ ]
    low = { }
        
    def visit(node):
        if node in low: return
    
        num = len(low)
        low[node] = num
        stack_pos = len(stack)
        stack.append(node)
    
        for successor in graph[node]:
            visit(successor)
            low[node] = min(low[node], low[successor])
        
        if num == low[node]:
            component = tuple(stack[stack_pos:])
            del stack[stack_pos:]
            result.append(component)
            for item in component:
                low[item] = len(graph)
    
    for node in graph:
        visit(node)
    
    return result


def Makegraph(edges):
    '''
    Convert a list of directed edged (start,end) to a graph connectivity dict.
    '''
    import itertools, operator
    
    edges.sort()
    # get all nodes involved in the graph
    nodes = set(itertools.chain.from_iterable(edges))
    # generate inital graph
    graph = dict.fromkeys(nodes,[])
    # group edges to set lists of successors for each node
    links = itertools.groupby(edges, operator.itemgetter(0))
    # convert iterable object to the graph dict
    link_graph = dict((i[0],[j[1] for j in list(i[1])]) for i in links)    
    # include nodes without successors
    graph.update(link_graph)

    return graph
    
    
if __name__ == '__main__':
    edges = [(0,1), (1,2), (2,0), (2,3), (3,3), (0,3), (1,4)]
    graph = Makegraph(edges)
    print 'graph is ', graph
    loops = GraphLoops(graph)
    print loops

def SuperNodes():
    pass
    
    
def tc(g):
    """ Given a graph @g, returns the transitive closure of @g """
    ret = {}
    for scc in GraphLoops(g):
            ws = set()
            ews = set()
            for v in scc:
                    ws.update(g[v])
            for w in ws:
                    assert w in ret or w in scc
                    ews.add(w)
                    ews.update(ret.get(w,()))
            if len(scc) > 1:
                    ews.update(scc)
            ews = tuple(ews)
            for v in scc:
                    ret[v] = ews
    return ret

    

    
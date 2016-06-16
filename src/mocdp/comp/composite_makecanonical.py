from collections import namedtuple
from contracts import contract
from contracts.utils import raise_wrapped
from mocdp.comp.composite import CompositeNamedDP
from mocdp.comp.connection import get_connection_multigraph
from mocdp.comp.flattening.flatten import cndp_flatten
from mocdp.comp.interfaces import NotConnected
from mocdp.exceptions import DPSemanticError
from networkx.algorithms.cycles import simple_cycles
import numpy as np
from mcdp_posets.poset_product import PosetProduct
from mocdp.comp.context import CResource, Connection, is_res_node_name, \
    is_fun_node_name

@contract(ndp=CompositeNamedDP)
def cndp_makecanonical(ndp):

    try:
        ndp.check_fully_connected()
    except NotConnected as e:
        msg = 'Cannot put in canonical form because not all subproblems are connected.'
        raise_wrapped(DPSemanticError, e, msg, compact=True)

    # First, we flatten it
    ndp = cndp_flatten(ndp)
    # then we compact it
    ndp = ndp.compact()

    # Check that we have some cycles
    G = get_connection_multigraph(ndp.get_connections())
    cycles = list(simple_cycles(G))
    if not cycles:
        msg = 'This problem has no cycles.'
        raise NotImplementedError(msg)

    # then we choose which edges to remove
    connections_to_cut = choose_connections_to_cut(
                            connections=ndp.get_connections(),
                            name2dp=ndp.get_name2ndp())

    print('connections to cut: %s' % connections_to_cut)

    connections_to_cut = list(connections_to_cut)
    n = len(connections_to_cut)
    names = list(['cut%d' % _ for _ in range(n)])
    ndp_inner = cndp_create_one_without_some_connections(ndp, connections_to_cut, names)
    return ndp_inner


@contract(names='list[N]', exclude_connections='list[N]')
def cndp_create_one_without_some_connections(ndp, exclude_connections, names):
    """ Creates a new CompositeNDP without some of the connections.
    A new function / resource pair is created for each cut connection. """
    from mocdp.comp.context import Context
    context = Context()
    
    print ndp
    print ndp.get_rnames()
    print ndp.get_fnames()
    for _name, _ndp in ndp.get_name2ndp().items():
        isf, fname = is_fun_node_name(_name)
        isr, rname = is_res_node_name(_name)

        if isf and fname in ndp.get_fnames():
            print('fname: %r' % fname)
            F = ndp.get_ftype(fname)
            context.add_ndp_fun_node(fname, F)
        elif isr and rname in ndp.get_rnames():
            print('rname: %r' % rname)
            R = ndp.get_rtype(rname)
            context.add_ndp_res_node(rname, R)
        else:
            print('regular: %r' % _name)
            context.add_ndp(_name, _ndp)

    for c in ndp.get_connections():
        if c in exclude_connections:
            continue
        print('adding connection %s' % str(c))
        context.connections.append(c)

    print('done')
    # for each cut connection
    for e, name in zip(exclude_connections, names):
        S = context.get_rtype(CResource(e.dp1, e.s1))
        fn = context.add_ndp_fun_node(name, S)
        rn = context.add_ndp_res_node(name, S)
        print rn
        c1 = Connection(e.dp1, e.s1, rn, name)
        c2 = Connection(fn, name, e.dp2, e.s2)
        context.connections.append(c1)
        context.connections.append(c2)
#         context.add_connection(c1)
#         context.add_connection(c2)

    return CompositeNamedDP.from_context(context)



def find_one(connections, a, b):
    for c in connections:
        if c.dp1 == a and c.dp2 == b:
            return c
    assert False

def choose_connections_to_cut(connections, name2dp):
    from mocdp.comp.connection import simple_cycles_as_edges

    # Compute the graph representation
    G = get_connection_multigraph(connections)

    from collections import defaultdict
    
    def space_weight(R):
        if isinstance(R, PosetProduct):
            return len(R.subs)
        else:
            return 1

    def edge_weight(e):
        (dp1, dp2) = e
        c = find_one(connections, dp1, dp2)
        R = name2dp[c.dp1].get_rtype(c.s1)
        return space_weight(R)

    edges_to_remove = enumerate_minimal_solution(G, edge_weight)
    connection_to_remove = [ _ for _ in connections if (_.dp1, _.dp2) in edges_to_remove]

    return connection_to_remove
# #
# #     # Returns the list of cycles as a sequence of edges
# #     c_as_e = simple_cycles_as_edges(G)
# #
# #     counts = defaultdict(lambda: 0)
# #     for cycle in c_as_e:
# #         for edge in cycle:
# #             counts[edge] += 1
# #
# #     ncycles = len(c_as_e)
# #     best_edge, ncycles_broken = max(list(counts.items()), key=lambda x: x[1])
#
#
#
#     its_connection = find_one(best_edge[0], best_edge[1])
#     F = name2dp[its_connection.dp1].get_rtype(its_connection.s1)
#     print('Min cut: breaking %d of %d cycles by removing %s, space = %s.' %
#         (ncycles_broken, ncycles, str(its_connection), F))
#     # print('its connection is %s' % str(its_connection))
#     # print('querying F = %s ' % name2dp[its_connection.dp1].get_rtype(its_connection.s1))
#     return its_connection


def enumerate_minimal_solution(G, edge_weight):
    """
        G: a graph
        edge_weight: a map from edge (i,j) of G to nonnegative weight
    """
    from mocdp.comp.connection import simple_cycles_as_edges
    
    State = namedtuple('State', 'cycles weight')
    # set of edges removed -> state 
    current_solutions = {} 
    current_partial_solutions = {}
    examined = set()
    
    freeze = frozenset
    
    # initial states
    all_edges = set(G.edges())
    
    current_partial_solutions[freeze([])] = State(cycles=simple_cycles_as_edges(G), weight=0.0)
    
    while current_partial_solutions:
        # choose the solution to expand with minimum weight
        removed, state = pop_solution_minimum_weight(current_partial_solutions)
        examined.add(removed)
        print('%s / %s / %s' % (len(current_solutions), len(current_partial_solutions), removed))

        # now look at edges that we could remove
        to_remove = all_edges - removed

        for edge in to_remove:
            new_weight = state.weight + edge_weight(edge)
            removed2 = set(removed)
            removed2.add(edge)
            removed2 = frozenset(removed2)

            if removed2 in examined:
                print('do not consider')
                continue

            cycles = [c for c in state.cycles if not edge in c]

            ss = State(cycles=cycles, weight=new_weight)
            if not cycles:
                current_solutions[removed2] = ss
            else:
                current_partial_solutions[removed2] = ss

    solutions = list(current_solutions)
    weights = [current_solutions[k].weight for k in solutions]
    best = solutions[np.argmin(weights)]
    state = current_solutions[best]

    print('best: %s %s' % (best, state))
    return best


def pop_solution_minimum_weight(sols):
    keys = list(sols)
    weights = [sols[_].weight for _ in keys]
    best = np.argmin(weights)
    k = keys[best]
    res = sols[k]
    del  sols[k]
    return k, res



# Returns the list of cycles as a sequence of edges
#     c_as_e = simple_cycles_as_edges(G)
#
#     counts = defaultdict(lambda: 0)
#     for cycle in c_as_e:
#         for edge in cycle:
#             counts[edge] += 1
#
#     ncycles = len(c_as_e)
#     best_edge, ncycles_broken = max(list(counts.items()), key=lambda x: x[1])
    
    
        
    
    


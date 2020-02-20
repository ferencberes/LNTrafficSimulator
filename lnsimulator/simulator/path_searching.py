import networkx as nx
import pandas as pd
import numpy as np
import copy
from collections import Counter

from .genetic_routing import GeneticPaymentRouter

def get_shortest_paths(init_capacities, G_origi, transactions, hash_transactions=True, cost_prefix="", weight="total_fee", required_length=None):
    G = G_origi.copy()# copy due to forthcoming graph capacity changes!!!
    capacity_map = copy.deepcopy(init_capacities)
    with_depletion = capacity_map != None
    shortest_paths = []
    total_depletions = dict()
    router_fee_tuples = []
    hashed_transactions = {}
    genetic_rounds = []
    for idx, row in transactions.iterrows():
        p, cost = [], None
        try:
            S, T = row["source"], row["target"] + "_trg"
            if (not S in G.nodes()) or (not T in G.nodes()):
                shortest_paths.append((row["transaction_id"], cost, len(p)-1, p))
                continue
            p = nx.shortest_path(G, source=S, target=T, weight=weight)
            if required_length != None:
                if len(p) > 2 and len(p)-1 < required_length:
                    # extend only non-direct short chanels!
                    gpr = GeneticPaymentRouter(required_length, G)#, router_weights)
                    _, _, p_new, num_rounds = gpr.run(p, size=100, best_ratio=0.25)
                    genetic_rounds.append(num_rounds)
                    if num_rounds != -1:
                        p = p_new
            if row["target"] in p:
                raise RuntimeError("Loop detected: %s" % row["target"])
            cost, router_fees, depletions = process_path(p, row["amount_SAT"], capacity_map, G,  "total_fee", with_depletion)
            if with_depletion:
                for dep_node in depletions:
                    total_depletions[dep_node] = total_depletions.get(dep_node, 0) + 1
            routers = list(router_fees.keys())
            router_fee_tuples += list(zip([row["transaction_id"]]*len(router_fees),router_fees.keys(),router_fees.values()))
            if hash_transactions:
                for router in routers:
                    if not router in hashed_transactions:
                        hashed_transactions[router] = []
                    hashed_transactions[router].append(row)
        except nx.NetworkXNoPath:
            continue
        except:
            raise
        finally:
            shortest_paths.append((row["transaction_id"], cost, len(p)-1, p))
    if hash_transactions:
        for node in hashed_transactions:
            hashed_transactions[node] = pd.DataFrame(hashed_transactions[node], columns=transactions.columns)
    elif required_length!=None:
        cnt = Counter(genetic_rounds)
        print(cnt.most_common())
    all_router_fees = pd.DataFrame(router_fee_tuples, columns=["transaction_id","node","fee"])
    return pd.DataFrame(shortest_paths, columns=["transaction_id", cost_prefix+"cost", "length", "path"]), hashed_transactions,  all_router_fees, total_depletions

def process_path(path, amount_in_satoshi, capacity_map, G, weight, with_depletion):
    routers = {}
    depletions = []
    N = len(path)
    for i in range(N-2):
        n1, n2 = path[i], path[i+1]
        routers[n2] = G[n1][n2][weight]
        if with_depletion:
            n2_removed = process_forward_edge(capacity_map, G, amount_in_satoshi, n1, n2)
            if n2_removed:
                depletions.append(n2)
            process_backward_edge(capacity_map, G, amount_in_satoshi, n2, n1)
    # last node in path is always a pseudo node
    n1, n2 = path[N-2], path[N-1].replace("_trg","")
    if with_depletion:
        n2_removed = process_forward_edge(capacity_map, G, amount_in_satoshi, n1, n2)
        if n2_removed:
            depletions.append(n2)
        process_backward_edge(capacity_map, G, amount_in_satoshi, n2, n1)
    return np.sum(list(routers.values())), routers, depletions

def process_forward_edge(capacity_map, G, amount_in_satoshi, src, trg):
    removed = False
    cap, fee, is_trg, total_cap = capacity_map[(src,trg)]
    if cap < amount_in_satoshi:
        raise RuntimeError("forward %i: %s-%s" % (cap,src,trg))
    if cap < 2*amount_in_satoshi: # cannot route more transactions
        removed = True
        G.remove_edge(src, trg)
        if is_trg:
            G.remove_edge(src, trg+'_trg')
    capacity_map[(src,trg)] = [cap-amount_in_satoshi, fee, is_trg, total_cap]
    return removed
    
def process_backward_edge(capacity_map, G, amount_in_satoshi, src, trg):
    if (src,trg) in capacity_map:
        cap, fee, is_trg, total_cap = capacity_map[(src,trg)]
        if cap < amount_in_satoshi: # it can route transactions again
            G.add_weighted_edges_from([(src,trg,fee)], weight="total_fee")
            if is_trg:
                G.add_weighted_edges_from([(src,trg+'_trg',0.0)], weight="total_fee")
        capacity_map[(src,trg)] = [cap+amount_in_satoshi, fee, is_trg, total_cap]

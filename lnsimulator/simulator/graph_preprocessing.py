import networkx as nx
import pandas as pd
import numpy as np

def prepare_edges_for_simulation(edges, amount_sat, drop_disabled, drop_low_cap, time_window=None, ts_upper_bound=None, verbose=True):
    """Preprocess LN graph snapshot with different edge filters."""
    E = len(edges)
    if ts_upper_bound != None:
        tmp_edges = edges[edges["last_update"] < ts_upper_bound].copy()
    else:
        tmp_edges = edges.copy()
    if verbose:
        print("Channel filter - invalid timestamp:", E - len(tmp_edges))
    # remove edges with capacity below threshold
    if drop_low_cap:
        tmp_edges = tmp_edges[tmp_edges["capacity"] >= amount_sat]
        if verbose:
            print("Channel filter - capacity:", E - len(tmp_edges))
        E = len(tmp_edges)
    # remove old channels
    if time_window != None:
        ts_lower_bound = tmp_edges["last_update"].max() - time_window
        tmp_edges = tmp_edges[tmp_edges["last_update"] >= ts_lower_bound]
        if verbose:
            print("Channel filter - recency:", E - len(tmp_edges))
        E = len(tmp_edges)
    # remove disabled edges
    if drop_disabled:
        tmp_edges = tmp_edges[~tmp_edges["disabled"]]
        if verbose:
            print("Channel filter - disabled:", E - len(tmp_edges))
        E = len(tmp_edges)
    # calculate edge costs
    tmp_edges["total_fee"] = calculate_tx_fee(tmp_edges, amount_sat)
    # aggregate multi-edges
    grouped = tmp_edges.groupby(["src","trg"])
    directed_aggr_edges = grouped.agg({
        "capacity":"sum",
        "total_fee":"mean",
    }).reset_index()
    if verbose:
        print("Total number of deleted directed channels:", len(edges) - len(tmp_edges))
        print("Number of remaining directed channels:", len(tmp_edges))
        print("Number of edges after aggregation: %i" % len(directed_aggr_edges))
    return directed_aggr_edges

def init_node_params(edges, providers, verbose=True):
    """Initialize source and target distribution of each node in order to drawn transaction at random later."""
    G = nx.from_pandas_edgelist(edges, source="src", target="trg", edge_attr=["capacity"], create_using=nx.DiGraph())
    active_providers = list(set(providers).intersection(set(G.nodes())))
    active_ratio = len(active_providers) / len(providers)
    if verbose:
        print("Total number of possible providers: %i" % len(providers))
        print("Ratio of active providers: %.2f" % active_ratio)
    degrees = pd.DataFrame(list(G.degree()), columns=["pub_key","degree"])
    total_capacity = pd.DataFrame(list(nx.degree(G, weight="capacity")), columns=["pub_key","total_capacity"])
    node_variables = degrees.merge(total_capacity, on="pub_key")
    #get_src_rayleigh_proba(node_variables)
    #get_trg_proba(node_variables, eps=0.95, active_providers)
    return node_variables, active_providers, active_ratio

def generate_graph_for_path_search(edges, transactions, amount_sat):
    """Generate pseudo edges and generate graph for path search."""
    targets = list(transactions["target"].unique())
    #sources = list(transactions["source"].unique())
    #participants = set(sources).union(set(targets))
    # drop edges with low capacity
    edges_tmp = edges[edges["capacity"]>=amount_sat].copy()
    # add pseudo targets
    ps_edges = edges_tmp[edges_tmp["trg"].isin(targets)].copy()
    ps_edges["trg"] = ps_edges["trg"].apply(lambda x: str(x) + "_trg")
    ps_edges["total_fee"] = 0.0
    ps_edges["fee_base_msat"] = 0.0
    ps_edges["fee_rate_milli_msat"] = 0.0
    # initialize transaction graph
    all_edges = pd.concat([edges_tmp, ps_edges], sort=False)
    # networkx versiom >= 2: from_pandas_edgelist
    G = nx.from_pandas_edgelist(all_edges, source="src", target="trg", edge_attr=["total_fee","capacity"], create_using=nx.DiGraph())
    return G

def calculate_tx_fee(df, amount_sat):
    # first part: fee_base_msat -> fee_base_sat
    # second part: milli_msat == 10^-6 sat : fee_rate_milli_msat -> fee_rate_sat
    return df["fee_base_msat"] / 1000.0 + amount_sat * df["fee_rate_milli_msat"] / 10.0**6

def init_capacities(edges, transactions, amount_sat, verbose=False):
    """Initialize capacity map for path search"""
    tx_targets = set(transactions["target"])
    # init capacity dict
    keys = list(zip(edges["src"], edges["trg"]))
    is_trg = edges["trg"].apply(lambda x: x in tx_targets)
    # [current_cap, total_fee, is_trg, total_cap]
    vals = [list(item) for item in zip([None]*len(edges), edges["total_fee"], is_trg, edges["capacity"])]
    capacity_map = dict(zip(keys,vals))
    # extract channels
    channels = set()
    for s, t in keys:
        if (s,t) in channels or (t,s) in channels:
            continue
        else:
            channels.add((s,t))
    edges_with_capacity = populate_capacities(channels, capacity_map, amount_sat)
    if verbose:
        print("Edges with capacity: %i->%i" % (len(edges),len(edges_with_capacity))) 
    return capacity_map, edges_with_capacity
    
def populate_capacities(channels, capacity_map, amount_sat):
    """Initialize the capacity state of each channel at random"""
    edge_records = []
    for src, trg in channels:
        c1 = capacity_map[(src,trg)][3]
        if (trg,src) in capacity_map:
            c2 = capacity_map[(trg,src)][3]
            cap = max(c1, c2)
            rnd = np.random.random()
            cap1, cap2 = cap * rnd, cap * (1.0-rnd)
            capacity_map[(trg,src)][0] = cap2
            if cap2 >= amount_sat:
                edge_records.append((trg, src, cap2, capacity_map[(trg,src)][1]))
        else:
            cap1 = c1
        capacity_map[(src,trg)][0] = cap1
        if cap1 >= amount_sat:
            edge_records.append((src, trg, cap1, capacity_map[(src,trg)][1]))
    return pd.DataFrame(edge_records, columns=["src","trg","capacity","total_fee"])

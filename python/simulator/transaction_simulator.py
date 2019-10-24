import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import sys, os, json

from .transaction_sampling import sample_transactions
from .graph_preprocessing import *
from .path_searching import get_shortest_paths

def shortest_paths_with_exclusion(capacity_map, G, cost_prefix, weight, hash_bucket_item):
    node, bucket_transactions = hash_bucket_item
    H = G.copy()
    H.remove_node(node)
    if node + "_trg" in G.nodes():
        H.remove_node(node + "_trg") # delete node copy as well
    new_paths, _, _, _ = get_shortest_paths(capacity_map, H, bucket_transactions,  hash_transactions=False, cost_prefix=cost_prefix, weight=weight)
    new_paths["node"] = node
    return new_paths

import functools
import concurrent.futures

def get_shortest_paths_with_node_removals(capacity_map, G, hashed_transactions, cost_prefix="", weight=None, threads=4):
    print(threads)
    if threads > 1:
        f_partial = functools.partial(shortest_paths_with_exclusion, capacity_map, G, cost_prefix, weight)
        executor = concurrent.futures.ProcessPoolExecutor(threads)
        alternative_paths = list(executor.map(f_partial, hashed_transactions.items()))
        executor.shutdown()
    else:
        alternative_paths = []
        for hash_bucket_item in tqdm(hashed_transactions.items(), mininterval=10):
            alternative_paths.append(shortest_paths_with_exclusion(capacity_map, G, cost_prefix, weight, hash_bucket_item))
    return pd.concat(alternative_paths)

class TransactionSimulator():
    def __init__(self, edges, providers, amount_sat, k, eps=0.8, drop_disabled=True, drop_low_cap=True, with_depletion=True, time_window=None, verbose=True):
        self.verbose = verbose
        self.with_depletion = with_depletion
        self.amount = amount_sat
        self.edges = prepare_edges_for_simulation(edges, amount_sat, drop_disabled, drop_low_cap, time_window, verbose=self.verbose)
        self.node_variables, self.providers, active_ratio = init_node_params(self.edges, providers, verbose=self.verbose)
        self.transactions = sample_transactions(self.node_variables, amount_sat, k, eps, self.providers)
        self.params = {
            "amount":amount_sat,
            "count":k,
            "epsilon":eps,
            "with_depletion":with_depletion,
            "drop_disabled":drop_disabled,
            "drop_low_cap": drop_low_cap,
            "time_window":time_window,
            "active_providers":len(self.providers),
            "active_ratio":active_ratio
        }
    
    def simulate(self, weight=None, with_node_removals=True, max_threads=8, excluded=[], required_length=None):
        if self.with_depletion:
            current_capacity_map, edges_with_capacity = init_capacities(self.edges, self.transactions, self.amount)
            G = generate_graph_for_path_search(edges_with_capacity, self.transactions, self.amount)
        else:
            current_capacity_map = None
            G = generate_graph_for_path_search(self.edges, self.transactions, self.amount)
        if len(excluded) > 0:
            print(G.number_of_edges(), G.number_of_nodes())
            for node in excluded:
                if node in G.nodes():
                    G.remove_node(node)
                pseudo_node = str(node) + "_trg"
                if pseudo_node in G.nodes():
                    G.remove_node(pseudo_node)
            print(G.number_of_edges(), G.number_of_nodes())
            print("Additional nodes were EXCLUDED!")
        if self.verbose:
            print("Graph and capacities were INITIALIZED")
            print("Using weight='%s' for the simulation" % weight)
            print("Transactions simulated on original graph STARTED..")
        shortest_paths, hashed_transactions, all_router_fees, total_depletions = get_shortest_paths(current_capacity_map, G, self.transactions, hash_transactions=with_node_removals, cost_prefix="original_", weight=weight, required_length=required_length)
        success_tx_ids = set(all_router_fees["transaction_id"])
        self.transactions["success"] = self.transactions["transaction_id"].apply(lambda x: x in success_tx_ids)
        if self.verbose:
            print("Transactions simulated on original graph DONE")
            print("Transaction succes rate:")
            print(self.transactions["success"].value_counts() / len(self.transactions))
            print("Length distribution of optimal paths:")
            print(shortest_paths["length"].value_counts())
        if with_node_removals:
            if self.verbose:
                print("Transactions simulated with node removals STARTED..")
            alternative_paths = get_shortest_paths_with_node_removals(current_capacity_map, G, hashed_transactions, weight=weight, threads=max_threads)
            if self.verbose:
                print("Transactions simulated with node removals DONE")
                print("Length distribution of optimal paths:")
                print(alternative_paths["length"].value_counts())
        else:
            alternative_paths = pd.DataFrame([])
        self.shortest_paths = shortest_paths
        self.alternative_paths = alternative_paths
        self.all_router_fees = all_router_fees
        return shortest_paths, alternative_paths, all_router_fees, total_depletions
    
    def export(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open('%s/params.json' % output_dir, 'w') as fp:
            json.dump(self.params, fp)
        length_distrib = self.shortest_paths["length"].value_counts()
        length_distrib.to_csv("%s/lengths_distrib.csv" % output_dir)
        total_income = get_total_income_for_routers(self.all_router_fees)
        total_income.to_csv("%s/router_incomes.csv" % output_dir, index=False)
        total_fee = get_total_fee_for_sources(self.transactions, self.shortest_paths)
        total_fee.to_csv("%s/source_fees.csv" % output_dir, index=True)
        if len(self.alternative_paths) > 0: 
            print(self.alternative_paths["cost"].isnull().value_counts())
        print("Export DONE")
        return total_income, total_fee
    
### process results ###

def get_total_income_for_routers(all_router_fees):
    grouped = all_router_fees.groupby("node")
    aggr_router_income = grouped.agg({"fee":"sum","transaction_id":"count"}).reset_index().sort_values("fee",ascending=False)
    return aggr_router_income.rename({"transaction_id":"num_trans"}, axis=1)

def get_total_fee_for_sources(transactions, shortest_paths):
    tmp_sp = shortest_paths[shortest_paths["length"]>0]
    trans_with_costs = transactions[["transaction_id","source"]].merge(tmp_sp[["transaction_id","original_cost"]], on="transaction_id", how="right")
    agg_funcs = dict(original_cost='mean', transaction_id='count')
    aggs = trans_with_costs.groupby(by="source")["original_cost"].agg(agg_funcs).rename({"original_cost":"mean_fee","transaction_id":"num_trans"}, axis=1)
    return aggs
"""
def calculate_node_influence(shortest_paths, alternative_paths):
    s_paths = shortest_paths.copy().drop("path", axis=1)
    a_paths = alternative_paths.copy().drop("path", axis=1)
    s_paths["original_cost"] = 1.0 / (1.0 + s_paths["original_cost"])
    a_paths["cost"] = 1.0 / (1.0 + a_paths["cost"])
    routing_diff = a_paths.merge(s_paths, on="transaction_id", how="left", suffixes=("","_original"))
    routing_diff = routing_diff.fillna(0.0)
    harmonic_sums = routing_diff.drop("transaction_id", axis=1).groupby(by="node").aggregate({"cost":"sum","original_cost":"sum"})
    harmonic_sums["cost_diff"] = harmonic_sums["original_cost"] - harmonic_sums["cost"]
    return harmonic_sums.sort_values("cost_diff", ascending=False), routing_diff

def aggregate_samples(experiment_files, snapshot_id):
    samples = []
    for i, f in enumerate(experiment_files[snapshot_id]):
        df = pd.read_csv(f)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df[~df["cost_diff"].isnull()]
        df["sample_id"] = i
        samples.append(df)
    df = pd.concat(samples, sort=True)
    mean_costs = df.groupby("node").mean().drop("sample_id", axis=1)
    return merge_with_other_metrics(mean_costs.sort_values("cost_diff", ascending=False), snapshot_id), df

def merge_with_other_metrics(mean_costs, snapshot_id, weight=None):
    cent = pd.read_csv("/mnt/idms/fberes/data/bitcoin_ln_research/centrality_scores/scores_%s_%i.csv" % (weight, snapshot_id))
    most_pop = pd.read_csv("/mnt/idms/fberes/data/bitcoin_ln_research/most_pop_nodes.csv")
    all_info = mean_costs.reset_index().merge(cent[["index","betw","deg","pr"]], left_on="node", right_on="index", how="left").drop("index", axis=1)
    all_info = all_info.merge(most_pop[["index",str(snapshot_id)]], left_on="node", right_on="index", how="left").drop("index", axis=1)
    all_info = all_info.rename({str(snapshot_id):"pop"}, axis=1)
    all_info = all_info.fillna(0)
    return all_info
"""

### optimal fee pricing ###

def inspect_base_fee_thresholds(ordered_deltas, pos_thresholds, min_ratio):
    thresholds = [0.0] + pos_thresholds
    original_income = ordered_deltas["fee"].sum()
    original_num_transactions = len(ordered_deltas)
    incomes, probas = [original_income], [1.0]
    # inspect only positive deltas
    for th in thresholds[1:]:
        # transactions that will still pay the increased base_fee
        df = ordered_deltas[ordered_deltas["delta_cost"] >= th]
        prob = len(df) / original_num_transactions
        probas.append(prob)
        # adjusted router income at the new threshold
        adj_income = df["fee"].sum() + len(df) * th
        incomes.append(adj_income)
        if prob < min_ratio:
            break
    return incomes, probas, thresholds, original_income, original_num_transactions

def visualize_thresholds(incomes, probas, thresholds, original_num_transactions):
    fig, ax1 = plt.subplots()
    x = thresholds[:len(incomes)]
    ax1.set_title(original_num_transactions)
    ax1.plot(x, incomes, 'bx-')
    ax1.set_xscale("log")
    ax2 = ax1.twinx()
    ax2.plot(x, probas, 'gx-')
    ax2.set_xscale("log")

def calculate_max_income(n, p_altered, shortest_paths, all_router_fees, visualize=False, min_ratio=0.0):
    trans = p_altered[p_altered["node"] == n]
    trans = trans.merge(shortest_paths[["transaction_id","original_cost"]], on="transaction_id", how="inner")
    trans = trans.merge(all_router_fees, on=["transaction_id","node"], how="inner")#'fee' column is merged
    # router could ask for this cost difference
    trans["delta_cost"] = trans["cost"] - trans["original_cost"]
    ordered_deltas = trans[["transaction_id","fee","delta_cost"]].sort_values("delta_cost")
    ordered_deltas["delta_cost"] = ordered_deltas["delta_cost"].apply(lambda x: round(x, 2))
    pos_thresholds = sorted(list(ordered_deltas[ordered_deltas["delta_cost"]>0.0]["delta_cost"].unique()))
    incomes, probas, thresholds, alt_income, alt_num_trans = inspect_base_fee_thresholds(ordered_deltas, pos_thresholds, min_ratio)
    if visualize:
        visualize_thresholds(incomes, probas, thresholds, alt_num_trans)
    max_idx = np.argmax(incomes)
    return thresholds[max_idx], incomes[max_idx], probas[max_idx], alt_income, alt_num_trans

def calc_optimal_base_fee(shortest_paths, alternative_paths, all_router_fees):
    # paths with length at least 2
    valid_sp = shortest_paths[shortest_paths["length"]>1]
    # drop failed alternative paths
    p_altered = alternative_paths[~alternative_paths["cost"].isnull()]
    #print("Path ratio that have alternative routing after removals: %f" % (len(p_altered) / len(alternative_paths)))
    num_routers = len(alternative_paths["node"].unique())
    num_routers_with_alternative_paths = len(p_altered["node"].unique())
    #print("Node ratio that have alternative routing after removals: %f" % (num_routers_with_alternative_paths / num_routers))
    routers = list(p_altered["node"].unique())
    opt_strategy = []
    for n in tqdm(routers, mininterval=5):
        opt_delta, opt_income, opt_ratio, origi_income, origi_num_trans = calculate_max_income(n, p_altered, valid_sp, all_router_fees, visualize=False)
        opt_strategy.append((n, opt_delta, opt_income, opt_ratio, origi_income, origi_num_trans))
    opt_fees_df = pd.DataFrame(opt_strategy, columns=["node", "opt_delta", "opt_income", "opt_traffic", "alt_income", "alt_traffic"])
    total_income = get_total_income_for_routers(all_router_fees).rename({"fee":"total_income","num_trans":"total_traffic"}, axis=1)
    merged_infos = total_income.merge(opt_fees_df, on="node", how="outer")
    merged_infos = merged_infos.sort_values("total_income", ascending=False)
    print(merged_infos.isnull().sum() / len(merged_infos))
    merged_infos = merged_infos.fillna(0.0)
    merged_infos["failed_traffic"] = merged_infos["total_traffic"] - merged_infos["alt_traffic"]
    merged_infos["failed_traffic_ratio"] = merged_infos["failed_traffic"] / merged_infos["total_traffic"]
    merged_infos["failed_income_ratio"] = (merged_infos["total_income"] - merged_infos["alt_income"]) / merged_infos["total_income"]
    merged_infos["income_diff"] = merged_infos.apply(lambda x: x["opt_income"] - x["alt_income"] +  x["failed_traffic"] * x["opt_delta"], axis=1)
    print(merged_infos.drop("node", axis=1).mean())
    return merged_infos, p_altered

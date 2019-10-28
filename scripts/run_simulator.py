import pandas as pd
import os, sys
sys.path.insert(0,"../python/")
import simulator.transaction_simulator as ts

print("# 1. Parameters")

experiment_id = "trial"
snapshot_id = 0
amount_sat = 60000
num_transactions = 7000
eps = 0.8
drop_disabled = True
drop_low_cap = True
with_depletion = True
find_alternative_paths = True

data_dir = "../ln_data/"
output_dir = "%s/%i/" % (experiment_id, snapshot_id)

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("# 2. Load data")

snapshots = pd.read_csv("%s/ln_snapshot_directed_multi_edges.csv" % data_dir)
node_meta = pd.read_csv("%s/1ml_meta_data.csv" % data_dir)
print("Data files were LOADED.")

providers = list(node_meta["pub_key"])
edges = snapshots[snapshots["snapshot_id"]==snapshot_id]

print("# 3. Simulation")

simulator = ts.TransactionSimulator(edges, providers, amount_sat, num/mnt/idms/fberes/data/LNdata_transactions, drop_disabled=drop_disabled, drop_low_cap=drop_low_cap, eps=eps, with_depletion=with_depletion)
transactions = simulator.transactions
shortest_paths, alternative_paths, all_router_fees, _ = simulator.simulate(weight="total_fee", with_node_removals=find_alternative_paths)
total_income, total_fee = simulator.export(output_dir)

print("# 4. Statistics")

print("Total income:", total_income.sum())

print("# 5. Analyze optimal routing fee for nodes")

if find_alternative_paths:
    opt_fees_df, p_altered = ts.calc_optimal_base_fee(shortest_paths, alternative_paths, all_router_fees)
    opt_fees_df.to_csv("%s/opt_fees.csv" % output_dir, index=False)

print("done")
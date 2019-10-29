import pandas as pd
import os, sys
sys.path.insert(0,"../python/")
from ln_utils import preprocess_json_file
import simulator.transaction_simulator as ts

data_dir = "../ln_data/"
max_threads = 2

amount_sat = 60000
num_transactions = 7000
eps = 0.8
drop_disabled = True
drop_low_cap = True
with_depletion = True
find_alternative_paths = True

def run_experiment(edges, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("\n# 2. Load meta data")
    node_meta = pd.read_csv("%s/1ml_meta_data.csv" % data_dir)
    providers = list(node_meta["pub_key"])

    print("\n# 3. Simulation")
    simulator = ts.TransactionSimulator(edges, providers, amount_sat, num_transactions, drop_disabled=drop_disabled, drop_low_cap=drop_low_cap, eps=eps, with_depletion=with_depletion)
    transactions = simulator.transactions
    shortest_paths, alternative_paths, all_router_fees, _ = simulator.simulate(weight="total_fee", with_node_removals=find_alternative_paths, max_threads=max_threads)
    total_income, total_fee = simulator.export(output_dir)
    
    print("\n# 4. Analyze optimal routing fee for nodes")
    if find_alternative_paths:
        opt_fees_df, p_altered = ts.calc_optimal_base_fee(shortest_paths, alternative_paths, all_router_fees)
        opt_fees_df.to_csv("%s/opt_fees.csv" % output_dir, index=False)
    print("\ndone")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        input_type = sys.argv[1]
        print("# 1. Load LN graph data")
        if input_type == "raw":
            json_file = sys.argv[2]
            directed_edges = preprocess_json_file(json_file)
        elif input_type == "preprocessed":
            snapshot_id = int(sys.argv[2])
            snapshots = pd.read_csv("%s/ln_edges.csv" % data_dir)
            directed_edges = snapshots[snapshots["snapshot_id"]==snapshot_id]
        else:
            raise ValueError("The first arguments must be 'raw' or 'preprocessed'!")
        output_folder = sys.argv[3]
        run_experiment(directed_edges, output_folder)
    else:
        print("You must support 3 input arguments:")
        print("   run_simulator.py raw <json_file_path> <output_folder>")
        print("OR")
        print("   run_simulator.py preprocessed <snapshot_id (int)> <output_folder>")
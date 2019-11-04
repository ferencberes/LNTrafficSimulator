import pandas as pd
import numpy as np

def sample_providers(node_variables, K, providers):
    provider_records = node_variables[node_variables["pub_key"].isin(providers)]
    nodes = list(provider_records["pub_key"])
    probas = list(provider_records["degree"] / provider_records["degree"].sum())
    return np.random.choice(nodes, size=K, replace=True, p=probas)

def sample_transactions(node_variables, amount_in_satoshi, K, eps, active_providers, verbose=False):
    nodes = list(node_variables["pub_key"])
    src_selected = np.random.choice(nodes, size=K, replace=True)
    if eps > 0:
        n_prov = int(eps*K)
        trg_providers = sample_providers(node_variables, n_prov, active_providers)
        trg_rnd = np.random.choice(nodes, size=K-n_prov, replace=True)
        trg_selected = np.concatenate((trg_providers,trg_rnd))
        np.random.shuffle(trg_selected)
    else:
        trg_selected = np.random.choice(nodes, size=K, replace=True)
    transactions = pd.DataFrame(list(zip(src_selected, trg_selected)), columns=["source","target"])
    transactions["amount_SAT"] = amount_in_satoshi
    transactions["transaction_id"] = transactions.index
    transactions = transactions[transactions["source"] != transactions["target"]]
    if verbose:
        print("Number of loop transactions (removed):", K-len(transactions))
        print("Merchant target ratio:", len(transactions[transactions["target"].isin(active_providers)]) / len(transactions))
    return transactions[["transaction_id","source","target","amount_SAT"]]
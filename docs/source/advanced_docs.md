# Advanced Documentation

In the steps below we show you some specific use cases of our LN traffic simulator.

We suppose that you have already 

- installed `lnsimulator` and downloaded the related LN data. If it is not the case then should follow the instructions in the [Getting Started](getting_started) section first.
- understood the data preparation steps needed for payment simulation. We refer you to the [Basic Documentation](simulator_docs) if you missed this step.

## Preparation

Quickly execute all steps (e.g. imports, loading channel and merchant data) needed before advanced experiments 

```
from lnsimulator.ln_utils import preprocess_json_file
import lnsimulator.simulator.transaction_simulator as ts

data_dir = "../ln_data/" # path to the ln_data folder that contains the downloaded data
directed_edges = preprocess_json_file("%s/sample.json" % data_dir)

import pandas as pd
node_meta = pd.read_csv("%s/1ml_meta_data.csv" % data_dir)
providers = list(node_meta["pub_key"])

# the number of simulated payments and the payment value is fixed in this notebook

amount = 60000
count = 7000
```

## Parameters explained

Here is the list of main parameters. **By the word "transaction" we refer to LN payments.**

| Parameter | Description | Default value |
|     :---      |   :---   | :---
| `amount` |  value of each simulated transaction in satoshis  | **Must be set** |
| `count`  | number of random transactions to sample  | **Must be set** |
| `epsilon` |  ratio of merchants among transactions endpoints  | 0.8 |
| `drop_disabled` | drop temporarily disabled channels | True |
| `drop_low_cap` | drop channels with capacity less than `amount` | True |
| `with_depletion` | the available channel capacity is maintained for both endpoints | True |

The following examples will help you to understand the effect of each parameter. As `amount` and `count` are very straightforward parameters we will start with how to set merchant ratio for payment receivers.

### Merchant ratio for payment receivers

The number of unique receivers is the highest when **receivers sampled uniformly at random** (`epsilon=0.0`) while you have the chance to send payments **only to merchants** (`epsilon=1.0`). In most of our experiments we sample merchant receivers with high probability (`epsilon=0.8`) but we also select random receivers as well with small probability.

```
only_merchant_receivers = ts.TransactionSimulator(directed_edges, providers, amount, count, epsilon=1.0)
many_merchant_receivers = ts.TransactionSimulator(directed_edges, providers, amount, count, epsilon=0.8)
uniform_receivers = ts.TransactionSimulator(directed_edges, providers, amount, count, epsilon=0.0)
print(only_merchant_receivers.transactions["target"].nunique())
print(many_merchant_receivers.transactions["target"].nunique())
print(uniform_receivers.transactions["target"].nunique())
```

### Control channel exclusion with `drop_disabled` and `drop_low_cap`

Channels can be temporarily disabled for a given snapshot while active for others. If you want to **enable disabled channels** in your experiments then use `drop_disabled=False`. But 

```
default_sim = ts.TransactionSimulator(directed_edges, providers, amount, count, drop_disabled=True, drop_low_cap=True)
with_disabled_sim = ts.TransactionSimulator(directed_edges, providers, amount, count, drop_disabled=False, drop_low_cap=True)
print(default_sim.edges.shape)
print(with_disabled_sim.edges.shape)
```

A payment can only be forwarded on a given channel if the channel capacity is at least the value of the payment (`drop_low_cap=True`). But in the simulation you have the possibility to disabled this condition (`drop_low_cap=False`).

```
with_lowcap_sim = ts.TransactionSimulator(directed_edges, providers, amount, count, drop_disabled=False, drop_low_cap=False)
print(with_lowcap_sim.edges.shape)
```

### Updating node balances with payments

Individual balances of LN nodes is a private data but `lnsimulator` can **keep track of capacity imbalances** (`with_depletion=True`) as payments are executed on the fly. After distributing capacities randomly between related channel endpoints (initialization step), our simulator can monitor whether a node has enough outbound capacity on a given channel to forward the upcoming payment with respect to the payment value. This feature has several advantages:

- ability to detect node capacity depletions in case of heavy one-way traffic
- better understanding of payment failures

In case you disable this feature (`with_depletion=False`) payments can pass a channel in a fixed direction infinitely many times as long as the payment value is at most the channel capacity.

In the next example we observe the payment failure ratio with respect to the `with_depletio` parameter.

```
sim_with_dep = ts.TransactionSimulator(directed_edges, providers, amount, count, with_depletion=True)
_, _, _, _ = sim_with_dep.simulate(weight="total_fee")


sim_wout_dep = ts.TransactionSimulator(directed_edges, providers, amount, count, with_depletion=False)
_, _, _, _ = sim_wout_dep.simulate(weight="total_fee")
```

Transaction success rates are lower if capacity depletion is enabled (`with_depletion=True`). This indicates that **there are channels with heavy one-way traffic**.

```
print("Succes rate with depletions:", sim_with_dep.transactions["success"].mean())
print("Succes rate without depletions:", sim_wout_dep.transactions["success"].mean())
```

## Advanced simulation features

In the past experiment after initializing your simulator the `simulate()` function executed cheapest path routing by default without modifying the available channel data. Now let's see some additional use cases.

```
sim = ts.TransactionSimulator(directed_edges, providers, amount, count)
```

### Routing algorithm

For now you can choose between two routing algorithms by setting the `weight` parameter

- **cheapest path** routing (`weight="total_fee"` - DEFAULT SETTING)
- **shortest path** routing (`weight=None`)

```
shortest_paths, _, _, _ = sim.simulate(weight=None)
cheapest_paths, _, _, _ = sim.simulate(weight="total_fee")
```

**Filter out payments that could not be routed (they are denoted with `length==-1`)**

Then observe the average path length for the simulated payments

```
print(shortest_paths[shortest_paths["length"]>0]["length"].mean())
print(cheapest_paths[cheapest_paths["length"]>0]["length"].mean())
```

### Node removal

You can observe the effects of node removals as well by providing a list of LN node public keys. In this case every channel adjacent to the given nodes will be removed during payment simulation. 

**In this example we exclude the top 5 nodes with highest routing income**

```
_, _, all_router_fees, _ = sim.simulate(weight="total_fee")
print("Succes rate BEFORE exclusion:", sim.transactions["success"].mean())

top_5_stats = all_router_fees.groupby("node")["fee"].sum().sort_values(ascending=False).head(5)
print(top_5_stats)
top_5_nodes = list(top_5_stats.index)
```

You can observe how the payment success rate dropped by removing 5 important routers

```
_, _, _, _ = sim.simulate(weight="total_fee", excluded=top_5_nodes)
print("Succes rate AFTER exclusion:", sim.transactions["success"].mean())
```

### Node capacity reduction

You can observe the traffic changes for a node by reducing its capacity to a given fraction of its original value. 

**In this example we reduce capacity to 10% of the top 5 nodes with highest routing income. Then we compare their new income with the original.**

```
_, _, reduced_fees, _ = sim.simulate(weight="total_fee", cap_change_nodes=top_5_nodes, capacity_fraction=0.1)
print("Succes rate AFTER capacity reduction:", sim.transactions["success"].mean())

new_stats = reduced_fees.groupby("node")["fee"].sum()
old_and_new = top_5_stats.reset_index().merge(new_stats.reset_index(), on="node", how="left", suffixes=("_old","_new"))
print(old_and_new.fillna(0.0))
```

## Longer path (genetic) routing

In our [paper](https://arxiv.org/abs/1911.09432) we proposed a genetic algorithm to find cheap paths with at least a given length (`required_length` parameter). By default genetic routing is disabled (`required_length=None`). 

**We note that..** 

- using a higher value for `required_length` could increase the running time significantly.
- payment paths with length 1 (direct channels) won't be forced to longer as with zero intermediary node there is no privacy issue here
- if the genetic algorithm cannot find a path with the required length then it will return a path that is lower than this bound

**In this example we will observe the path length distribution for different values of the `required_length` parameter**

```
sim_for_routing = ts.TransactionSimulator(directed_edges, providers, amount, count)

min_path_l = [2,3,4]
length_distrib_map = {}

for length_value in min_path_l:
    cheapest_paths, _, _, _ = sim.simulate(weight="total_fee", required_length=length_value)
    length_distrib_map[length_value] = cheapest_paths["length"].value_counts()
    print(length_value)
```

Observe the fraction of path with a given length (rows). The columns represent values of the `required_length` parameter. **The fraction of path in (3,3) and (4,4) cell of the heatmap are indeed high due to longer path routing.** We note that the row with index -1 represent the fraction of failed payments.

```
import seaborn as sns

distrib_df = pd.DataFrame(length_distrib_map)
distrib_df = distrib_df / distrib_df.sum()
sns.heatmap(distrib_df.loc[[-1,1,2,3,4]], cmap="coolwarm", annot=True)
```

## Base fee optimization

In the Lightning Network data that we observed more than 60\% of the nodes charged the default base fee. From a node's position in the network `lnsimulator` can estimate the base fee increment needed to achieve optimal routing by setting `with_node_removals=True` and calling `calc_optimal_base_fee` function afterwards. **For now optimal base fee search is enabled only for cheapest path routing (`weight="total_fee`). We also recommend you apply parallelization by setting a higher value for the `max_threads` parameter.**

```
sim_fee_opt = ts.TransactionSimulator(directed_edges, providers, amount, count)
shortest_paths, alternative_paths, all_router_fees, _ = sim_fee_opt.simulate(weight="total_fee", with_node_removals=True, max_threads=2)
opt_fee_df, _ = ts.calc_optimal_base_fee(shortest_paths, alternative_paths, all_router_fees)
print(opt_fee_df.head())
```

The result of `calc_optimal_base_fee` contains the following informations.

| Column | Description |
|     :---      |   :---   |
| node | LN node public key |
| total_income | routing income |
| total_traffic | number of routed transactions |
| failed_traffic_ratio | ratio of failed transactions out of `total_traffic` payments if `node` is removed from LN  |
| opt_delta | estimated optimal increase in base fee |
| income_diff | estimated increase in daily routing income after applying optimal base fee increment |

In the next step we transform the `opt_delta` column into a categorical feature that represent the increment magnitude.

```
def to_category(x):
    if x > 100:
        return 3
    elif x > 10:
        return 2
    elif x > 0:
        return 1
    else:
        return 0
    
print("The magnitude distribution of base fee increments:")
print(opt_fee_df["opt_delta"].apply(to_category).value_counts())
```

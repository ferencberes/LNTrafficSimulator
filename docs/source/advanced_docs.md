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

# Other

## 1. Transaction fee optimization

## 2. Capacity optimization

## 3. Node removal

## 4. Genetic payment routing




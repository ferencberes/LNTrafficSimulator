# Basic Documentation

In the steps below we suppose that you have already installed `lnsimulator` and downloaded the related LN data.
If it is not the case then should follow the instructions in the [Getting Started](getting_started) section first.

## 1. Prepare LN data

In order to run the simulation you need to provide LN snapshots as well as information about merchants nodes.

### LN snapshots

The network structure is fed to `lnsimulator` in the form of LN snapshots. Raw JSON files as well as preprocessed payment channel data can be used as input.

#### a.) Load data from JSON file

```python
from lnsimulator.ln_utils import preprocess_json_file

data_dir = "..." # path to the ln_data folder that contains the downloaded data
directed_edges = preprocess_json_file("%s/sample.json" % data_dir)
```

#### b.) Load preprocessed LN snapshots

In this case you should select data related to a given daily snapshot

```python
import pandas as pd
snapshot_id = 0
snapshots = pd.read_csv("%s/ln_edges.csv" % data_dir)
directed_edges = snapshots[snapshots["snapshot_id"]==snapshot_id]
```

Note that the preprocessed data format is identical to the output of the `preprocess_json_file` function.

### Merchants

We provided the list of LN merchants that we used in our experiments. This merchant information was collected in early 2019.

```python
import pandas as pd
node_meta = pd.read_csv("%s/1ml_meta_data.csv" % data_dir)
providers = list(node_meta["pub_key"])
```

## 2. Configuration

First we give you the list of main parameters. **By the word "transaction" we refer to LN payments.**

| Parameter | Description |
|     :---      |   :---   |
| `amount` |  value of each simulated transaction in satoshis  |
| `count`  | number of random transactions to sample  |
| `epsilon` |  ratio of merchants among transactions endpoints  |
| `drop_disabled` | drop temporarily disabled channels |
| `drop_low_cap` | drop channels with capacity less than `amount` |
| `with_depletion` | the available channel capacity is maintained for both endpoints |

You can initialize the traffic simulator by providing the network structure, merchants information and the former parameters.

```python
import lnsimulator.simulator.transaction_simulator as ts

amount = 60000
count = 7000
epsilon = 0.8
drop_disabled = True
drop_low_cap = True
with_depletion = True

simulator = ts.TransactionSimulator(directed_edges, providers, amount, count, drop_disabled=drop_disabled, drop_low_cap=drop_low_cap, eps=epsilon, with_depletion=with_depletion)
```

## 3. Estimating daily income and traffic

### i.) Transactions

The simulator samples a set of random transactions (during the initialization) that will be used for the estimation of daily node traffic and routing income. You can access the sampled transactions in the form of a `pandas.DataFrame`.

```python
transactions = simulator.transactions
print(transactions.head())
print(transactions.shape)
```

### ii.) Run simulation

In this step the simulator searches for cheapest payment paths from transaction senders to its receivers. Channel capacity changes are well maintained during the simulation. 

```python
_, _, all_router_fees, _ = simulator.simulate(weight="total_fee", with_node_removals=False)
print(all_router_fees.head())
```

### iii.) Results

After payment simulation you can export the results as well as calculate traffic and income statistics for LN nodes.

```python
output_dir = "test"
total_income, total_fee = simulator.export(output_dir)

total_income.set_index("node").head(10)
```

You can search for the identity of these nodes on [1ml.com](https://1ml.com).

**In order to get stable daily LN node statistics, we recommend to run the simulator for multiple times over several consecutive snapshots!**


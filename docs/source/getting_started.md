# Getting started

By executing the steps below you can set up `lnsimulator` for your environment in a few minutes.

## Requirements

- UNIX or macOS environment
    - For macOS users: you need to have wget (brew install wget)
- This package was developed in Python 3.5 (conda environment) but it works with Python 3.6 and 3.7 as well.

## Install

After cloning the [repository](https://github.com/ferencberes/LNTrafficSimulator) from GitHub you can install the simulator with `pip`.

```bash
git clone https://github.com/ferencberes/LNTrafficSimulator.git
cd LNTrafficSimulator
pip install .
```

## Data

By providing daily LN snapshots as input **(you can bring and use your own!)**, our simulator models the flow of daily transactions.

### i.) Download

You can download the data files, that we used in our research by executing the following command:

#### a.) Linux
```bash
bash ./scripts/download_data.sh
ls ln_data
```
#### b.) macOS
```bash
sh ./scripts/download_data.sh
ls ln_data
```

You can also download the compressed data file with this [link](https://dms.sztaki.hu/~fberes/ln/ln_data_2019-10-29.zip).

### ii.) Content

The *download_data.sh* script downloads 4 data files into the *ln_data* folder with the following content:

| File | Simulator input? | Content |
|     :---      |   :---:   |   :---   |
| **sample.json** | Yes | sample JSON file containing a daily LN snapshot |
| **ln_edges.csv** | Yes | preprocessed LN snapshots in the form of a directed graph |
| **1ml_meta_data.csv** | Yes | merchant meta data that we downloaded from [1ml.com](https://1ml.com/) |
| **ln.tsv** | No | edge stream data about LN channels |

## First example

Execute the following code to see whether your configuration was successful.

```python
from lnsimulator.ln_utils import preprocess_json_file
import lnsimulator.simulator.transaction_simulator as ts

data_dir = "..." # path to the ln_data folder that contains the downloaded data
amount = 60000
count = 7000
epsilon = 0.8
drop_disabled = True
drop_low_cap = True
with_depletion = True
find_alternative_paths = False

print("# 1. Load LN graph data")
directed_edges = preprocess_json_file("%s/sample.json" % data_dir)

print("\n# 2. Load meta data")
node_meta = pd.read_csv("%s/1ml_meta_data.csv" % data_dir)
providers = list(node_meta["pub_key"])

print("\n# 3. Simulation")
simulator = ts.TransactionSimulator(directed_edges, providers, amount, count, drop_disabled=drop_disabled, drop_low_cap=drop_low_cap, eps=epsilon, with_depletion=with_depletion)
transactions = simulator.transactions
_, _, all_router_fees, _ = simulator.simulate(weight="total_fee", with_node_removals=find_alternative_paths, max_threads=1)

print(all_router_fees.head())
print("Done")
```

If your configuration works then you should proceed to the detailed [documentation](simulator_docs) of the LN traffic simulator.

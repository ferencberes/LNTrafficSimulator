# LNTrafficSimulator

This repository contains the Lightning Network (LN) traffic simulator used in the cryptoeconomic research of [Ferenc Béres](https://github.com/ferencberes), [István András Seres](https://github.com/seresistvanandras) and András A. Benczúr.

# Introduction

In our work, we designed a traffic simulator to empirically study LN’s transaction fees and privacy provisions. The simulator relies only on publicly available data of the network structure and capacities, and generates transactions under assumptions that we validated based on information spread by  [blog posts](https://www.trustnodes.com/2019/08/20/guy-makes-20-a-month-for-locking-5-million-worth-of-bitcoin-on-the-lightning-network?fbclid=IwAR2-p8nWdg0ayO9S0Uz7qg3wmh_A8Wy6ueX8r3dLQvDTyJaj1ReSbYalnWI) of LN node owners.

# Cite

**A link for our pre-print paper will be published here in a few days.**

# Data

By providing daily LN snapshots as input, our simulator models the flow of daily transactions. You can download the data files, that we used in our research by executing the following command:

```bash
bash ./scripts/download_data.sh
ls ln_data
```
After running the *download_data.sh* script three data files can be observed in the *ln_data* folder:

| File | Simulator input? | Content |
|     :---      |   :---:   |   :---   |
| **ln_snapshot_directed_multi_edges.csv** | Yes | preprocessed LN snapshots in the form of a directed graph |
| **1ml_meta_data.csv** | Yes | merchant meta data that we downloaded from [1ml.com](https://1ml.com/) |
| **sample.json** | Yes | sample json file containing a daily LN snapshot. It can be used as input to our traffic simulator but *it needs further preprocessing!* |
| **ln.tsv** | No | edge stream data about LN channels |

You can also download the compressed data file with this [link](https://dms.sztaki.hu/~fberes/ln/ln_data_2019-10-29.zip).

# Requirements

- UNIX environment
- **Python 3.5** conda environment with the following packages installed:
    - **data processing:** pandas, numpy, networkx, matplotlib
    - **general:** sys, os, json, copy, tqdm, collections, functools, concurrent 

# Usage

**You must download the data as described in the Data section to use our simulator!**

## i.) Parameters:

| Parameter | Description |
|     :---      |   :---   |
| `amount_sat` |  value of each simulated transaction in satoshis  |
| `num_transactions`  | number of random transactions to sample  |
| `eps` |  ratio of merchants in the endpoints of the random transactions  |
| `drop_disabled` | drop temporarily disabled channels |
| `drop_low_cap` | drop channels with capacity less than `amount_sat` |
| `with_depletion` | the available channel capacity is maintained for each endpoint |
| `find_alternative_paths` | execute base fee optimization step. **Note:** runtime decreases significantly if this step is disabled! |

You can set the value of these parameters in the simulator [script](scripts/run_simulator.py).


## ii.) Execution

You can run our LN traffic simulator in two different settings. 

If you have **multiple CPUs** at your disposal then we recommend setting a higher value of *max_threads* in the simulator [script](scripts/run_simulator.py).

### a.) Load data from preprocessed file

The default input format of the simulator is a directed graph representation of LN snapshots. In this case you must provide the *snapshot_id* (e.g. 0) and the output folder as parameters.

```bash
cd scripts
python run_simulator.py preprocessed 0 YOUR_OUTPUT_DIR
```

### b.) Load data from json file

You can execute the simulator on custom data as well, by providing daily LN snapshot as a json file (e.g. [lnd](https://graph.lndexplorer.com/api/graph)). See the example below:

```bash
cd scripts
python run_simulator.py raw ../ln_data/sample.json YOUR_OUTPUT_DIR
```

## iii.) Output

After execution you will find the output files in the provided YOUR_OUTPUT_DIR folder. The content of these files are as follows:

| File | Content |
|     :---      |   :---   |
| params.json | Traffic simulator parameter values |
| lengths_distrib.csv | Length distribution of simulated transactions. **Note:** the length is marked -1 if the payment failed (there was no available path for routing) |
| router_incomes.csv | Contains the total routing income (satoshi) and number of routed payments for LN nodes in the simulation |
| source_fees.csv | Contains the mean transaction costs (satoshi) and number of sent payments for transaction initiators nodes |
| opt_fees.csv | For each router the estimated optimal increase in base fee (`opt_delta`) and gain in daily routing income (`income_diff`) is shown along with several other statistics |


**In order to get stable daily LN node statistics, we recommend to run the simulator for multiple times over several consecutive snapshots!**


# Acknowledgements

We are grateful to Antoine Le Calvez (Coinmetrics) and Altangent Labs for kindly providing us their edge stream data and daily graph snapshots.
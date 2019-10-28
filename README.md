# LNTrafficSimulator

This repository contains the Lightning Network (LN) traffic simulator used in the cryptoeconomic research of [Ferenc Béres](https://github.com/ferencberes), [István András Seres](https://github.com/seresistvanandras) and András A. Benczúr.

# Introduction

In our work, we designed a traffic simulator to empirically study LN’s transaction fees and privacy provisions. The simulator relies only on publicly available data of the network structure and capacities, and generates transactions under assumptions that we validated based on information spread by  [blog posts](https://www.trustnodes.com/2019/08/20/guy-makes-20-a-month-for-locking-5-million-worth-of-bitcoin-on-the-lightning-network?fbclid=IwAR2-p8nWdg0ayO9S0Uz7qg3wmh_A8Wy6ueX8r3dLQvDTyJaj1ReSbYalnWI) of LN node owners.

**A link for our pre-print paper will be published here in a few days.**

# Data

By providing daily LN snapshots as input, our simulator models the flow of daily transactions. You can download the data files, that we used in our research by executing the following command:

```bash
bash ./scripts/download_data.sh
ls ln_data
```
After running the *download_data.sh* script three data files can be observed in the *ln_data* folder:

- **ln_snapshot_directed_multi_edges.csv:** preprocessed LN snapshots in the form of a directed graph (simulator input file)
- **1ml_meta_data.csv** merchant meta data that we downloaded from [1ml.com](https://1ml.com/) (simulator input file)
- **ln.tsv:** edge stream data about LN channels

You can also download the compressed data file with this [link](https://dms.sztaki.hu/~fberes/ln/ln_data.zip).

## Acknowledgements

We are grateful to Antoine Le Calvez (Coinmetrics) and Altangent Labs for kindly providing us their edge stream data and daily graph snapshots.

# Requirements

- UNIX environment
- **Python 3.5** conda environment with the following packages installed:
    - pandas, numpy, networkx, matplotlib
    - sys, os, json, copy, tqdm, collections 

# Usage

**You must download the data as described in the Data section to use our simulator!**

You can run our LN traffic simulator from the terminal:
```bash
cd scripts
python run_simulator.py
```

After execution you will find the output files in the *./script/trial/* folder.

### Main simulator parameters:

- **experiment_id:** name of the output folder
- **snapshot_id:** which snapshot to use for traffic simulation
- **amount_sat:** the value of each simulated transaction in satoshis
- **num_transactions:** the number of random transactions to sample
- **eps**: ratio of merchants in the endpoints of the random transactions

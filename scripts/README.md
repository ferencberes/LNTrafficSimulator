# Detailed output file contents

In order to get stable daily LN node statistics, we recommend to run the simulator for multiple times over several consecutive snapshots. **Node statistics in each output file below are restricted to a single traffic simulator experiment!**

## lengths_distrib.csv

Distribution of payment path length for the sampled transactions. Due to the source routing nature of LN, we assumed that transactions are executed on the cheapest path between the sender and the recipient.

| Column | Description |
|     :---      |   :---   |
| First | Payment path length |
| Second | Number of sampled transactions with given length |

**Note:** the length is marked -1 if the payment failed (there was no available path for routing)

**Note:** the sum of transactions in the second column could be less then the predefined number of payments to simulate. The difference is the number of randomly sampled loop transactions with identical sender and recipient node.

## router_incomes.csv

Contains statistics on nodes that forwarded payments in the simulation. We refer to these nodes as **routers**.

| Column | Description |
|     :---      |   :---   |
| node | LN node public key |
| fee | routing income |
| num_trans | number of routed transactions |

## source_fees.csv

Contains statistics on payment initiator nodes (senders).

| Column | Description |
|     :---      |   :---   |
| source | LN node that initiated the payment (sender node) |
| num_trans | the number of transactions initiated by this node in the simulation |
| mean_fee | the mean transaction cost per payment |

## opt_fees.csv

Contains several estimated statistics for router nodes with regard to base fee optimization.

| Column | Description |
|     :---      |   :---   |
| node | LN node public key |
| total_income | routing income |
| total_traffic | number of routed transactions |
| failed_traffic_ratio | ratio of failed transactions out of `total_traffic` payments if `node` is removed from LN  |
| opt_delta | estimated optimal increase in base fee |
| income_diff | estimated increase in daily routing income after applying optimal base fee increment |

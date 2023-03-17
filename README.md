# Description
This aim of this assignment is to build a discrete-event simulator for a P2P cryptocurrency network
- `block.py`        - Block structure
  - Contains block id, creator id, id of previous block, creation time, transactions, length from genesis block, balances of each peer and some other miscellaneous fields for implementation purposes 

- `transaction.py`  - Transaction structure
  - Contains txn id, sender id, receiver id, amount
  - Also contains a message of the form :
    - TxnID: $\textrm{ID}_x$ pays $\textrm{ID}_y$ C coins, if it is a normal transaction
    - TxnID: $\textrm{ID}_k$ mines C coins, if it is a coinbase transaction
  - Contains some other miscellaneous fields for implementation purposes

- `network.py` - Network structure
  - The network is created using the Networkx package in python
  - A graph of a given number of nodes is created to model the network
  - The graph is created such that each node is connected to atleast 4 and atmost 8 other nodes 
  - All the nodes have been given different attributes like cpu power, speed, hashing capabilities etc. to model them as peers
  - Simulates latencies

- `node.py`   - To represent a peer 
  - Contains local tree structure of blockchain
  - Manages its own transaction pool
  - Validates other blocks and adds it to its local chain
  - Mines new blocks on its local longest chain
  - Simulates transaction generation and PoW delays

- `event.py`         - Models 4 types of events
  - create_transaction - This event is responsible for creating transactions
  - receive_transactions - This event is responsible for receiving transactions to its neighbors
  - forward_transactions - This event is responsible for forwarding transactions to its neighbors
  - mine_block - This event is responsible for mining a block
  - forward_block - This event is responsible for listening for forwarding blocks to its neighbors
  - receive_block - This event is responsible for receiving blocks from its neighbors

- `simulate.py`    - Simulates Peers' interaction
  - Generates and simulates the blockchain network
  - Maintains the central priority queue which contains the events
  - Executes the events step by step
  - Initializes the queue at the start with a few transaction generate and mine block events

- `main.py`         - Main function
  - Takes in commandline arguments
  - Calls and runs the simulator
  - Dumps the blockchain trees into folders

# Instructions to run
In the source directory run `python3 main.py -n [nodes] -z [zeta] -z0 [low_cpu] -z1 [low_speed] -T [Ttx] -I [interarrival_block] -t [time] --type [type] -v -d -s -p -a [adversary_hashing]` \
For eg: `python3 main.py -n 35 -z 70 -z0 10 -z1 40 -T 10 -I 6 -t 4000 --type 1 -v -d -s -p -a 10` \
The commandline argument options are as follows:
- `-n or --nodes` : Number of nodes/peers (Use number of nodes to be $\geq 15$ to be safe) (defaults to 25)
- `-z or --zeta` : Percentage of nodes the adversary is connected to (defaults to 50)
- `-z0 or --low_cpu` : Percentage of slow nodes (defaults to 0)
- `-z1 or --low_speed` : Percentage of low CPU nodes (defaults to 0)
- `-T or --Ttx` : Mean transaction interarrival time (defaults to 10)
- `-I or --interarrival_block` : Mean block interarrival time (defaults  to 4)
- `-t or --time` : The amount of time to run the simulation for (defaults to 1000)
- `--type` : The type of simulation to run. 0 for normal simulation, 1 for selfish mining and 2 for stubborn mining (defaults to 0)
- `-v or --visualize` : To see the blockchain tree for the first five nodes (stores False)
- `-d or --dump` : To dump the blockchain tree and the networkx graph (stores False)
- `--normal` : To run a normal simulation (stores False)
- `-s or --save_progress` : To save the progress of the blockchain for node 0 and node 1.
- `-p or --print` : To print the progress of the simulation to the terminal (stores False)
- `-a or --adversary_hashing` : The percentage of hash power the adversary has


After all the steps are completed, the blockchain tree, blockchain tree dictionary and the networkx graph converted to PNGs are saved to the directories blockchain_tree, blockchain_tree_dict and networkx_graph respectively. \
Also the progress of the blockchain is saved to the directory progress_0 for node 0 and progress_1 for node 1. \
The conversion from networkx graphs to PNGs may take a while depending upon the number of nodes. 

NOTE: The .txt files contain Blockchain in the following format Block_\<Block_ID\>_\<Time at which block was received at the node\>

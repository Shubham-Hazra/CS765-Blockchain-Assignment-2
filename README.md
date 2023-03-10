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
  - CreateTXN - This event is responsible for creating transactions
  - ReceiveTXN - This event is responsible for forwarding transactions to its neighbors
  - MineBlock - This event is responsible for mining a block
  - ForwardBlock - This event is responsible for listening for forwarding blocks to its neighbors

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
In the source directory run `python3 main.py --n [n] --z0 [z0] --z1 [z1] --Ttx [Ttx] --I [I] --steps [steps]` \
For eg: `python3 main.py --n 100 --z0 10 --z1 40 --Ttx 10 --I 60 --steps 100000` \
Where:
- `n` : Number of nodes/peers (Use number of nodes to be $\geq 15$ to be safe) (defaults to 50)
- `z0` : Percentage of slow nodes (defaults to 10)
- `z1` : Percentage of low CPU nodes (defaults to 40)
- `Ttx` : Mean transaction interarrival time (defaults to 10)
- `I` : Mean block interarrival time (defaults  to 60)
- `steps` : The number of steps to run the simulation for (defaults to 10000)

After all the steps are completed, the blockchain tree, blockchain tree dictionary and the networkx graph converted to PNGs are saved to the directories blockchain_tree, blockchain_tree_dict and networkx_graph respectively. \
The conversion from networkx graphs to PNGs may take a while depending upon the number of nodes. 

NOTE: The .txt files contain Blockchain in the following format Block_\<Block_ID\>_\<Time at which block was received at the node\>

import random
import sys
from copy import deepcopy
from queue import PriorityQueue

from treelib import Node, Tree

from block import Block
from event import CreateTXN, Event, ForwardBlock, MineBlock, ReceiveTXN
from network import Network


class Simulator:
    def __init__(self, n,zeta,z1, Ttx, I, max_steps, simulation_type):
        self.N = Network(n,zeta,self.z0,z1,I)
        self.z0 = 50 # Percentage of slow nodes
        self.z1 = z1 # Percentage of low CPU nodes
        self.Ttx = Ttx # Mean transaction interarrival time
        self.I = I # Mean block interarrival time
        self.txn_id = 0
        self.block_id = 1
        self.mining_txn_id = -1
        self.num_min_events = 0
        self.zeta = zeta
        self.simulation_type = simulation_type
        self.events = PriorityQueue()
        self.global_transactions = {} # To store th TXN object indexed by the unique ID of the TXN
        self.global_Blocks = {} 
        self.global_Blocks["Block_0"] = Block(None,None,None,None,0,[100]*self.N.num_nodes,0,0)
        self.curr_time = 0 # Stores the timestamp of the current event being run
        self.initialize_events()
        self.run(max_steps)
        self.print_blockchains()
        self.visualize()
        
    # VERIFIED
    def initialize_events(self):
        print(len(self.N.nodes))
        for node in self.N.nodes:
            self.events.put(CreateTXN(
                node.pid, node.pid, 0, self.transaction_delay()
            ))
        # nodes_to_mine = random.sample(self.N.nodes,5) # HYPERPARAMETER HERE TO TUNE
         
        for node in self.N.nodes[0:1]:
            # Randomly choosing a node and starting the mining process
            # self.num_min_events+=1
            PoW_delay = node.get_PoW_delay()
            block = Block(node.pid, "Block_0", PoW_delay,[], self.N.num_nodes,[100]*self.N.num_nodes, self.block_id,1 )
            self.block_id+=1
            self.events.put(ForwardBlock(block, node.pid, node.pid, 0, PoW_delay))
    
    # VERIFIED
    def transaction_delay(self):
        return random.expovariate(1 / self.Ttx)
    
    # VERIFIED
    def run(self, max_steps = 10000):
        step_count = 0
        while step_count <= max_steps:
            if not self.events.empty():
                # Executing other events
                current_event = self.events.get()
                self.curr_time = current_event.run_time
            elif self.events.empty() and step_count <= max_steps:
                node_list = random.sample(self.N.nodes,1)[0:6]
                for node in node_list:
                    if random.random() > 0.9:
                        self.events.put(CreateTXN(
                        node.pid, node.pid, self.curr_time, self.curr_time + self.transaction_delay()
                        ))
                    else:
                        last_block = node.find_longest_chain()[-1]
                        PoW_delay = node.get_PoW_delay()

                        if not node.txn_pool:
                            print("MINING UNSUCCESSFUL: No TXN to include")
                            continue

                        txn_to_include = node.get_TXN_to_include()

                        # To terminate the block mining process if the node has no TXNs to include in the block        
                        if not txn_to_include:
                            print("MINING UNSUCCESSFUL: No TXN to include")
                            continue

                        block = Block(node.pid, last_block, PoW_delay,txn_to_include, self.N.num_nodes,deepcopy(self.global_Blocks[last_block].balances), self.block_id,1 )
                        self.global_Blocks[block.block_id] = block
                        self.block_id+=1
                        self.events.put(ForwardBlock(block, node.pid, node.pid, 0, PoW_delay))
                current_event = self.events.get()
                self.curr_time = current_event.run_time
            else:
                print("Simulation Complete!!")
                break
            print("Step Count: ", step_count)
            current_event.addEvent(self.N, self)
            step_count+=1

    # VERIFIED
    def print_blockchains(self):
        for node in self.N.nodes[0:6]:
            node.print_blockchain()

    # VERIFIED
    def visualize(self):
        tree = Tree()
        node = self.N.nodes[0]
        tree.create_node("Block_0", "Block_0")
        for block in node.blockchain_tree.keys():
            if block == "Block_0":
                continue
            tree.create_node(block,block, parent = node.blockchain_tree[block]['parent'])
        tree.show()


# Test
if __name__ == '__main__':
    S = Simulator(100, 10, 30, 1000, 6, 10000)
# S.run(10)
# node = random.sample(self.N.nodes,1)[0]
# if random.random() > 0.8:
#     self.events.put(CreateTXN(
#     node.pid, node.pid, 0, self.transaction_delay()
#     ))
# else:
#     # Randomly choosing a node and starting the mining process
#     self.events.put(MineBlock(
#     node.pid, node.pid, 0, node.get_PoW_delay()
#     ))

# elif self.num_min_events == 0 and step_count <= max_steps:
# node_list = random.sample(self.N.nodes,1)[0:6]
# for node in node_list:
#     if random.random() > 0.95:
#         self.events.put(CreateTXN(
#         node.pid, node.pid, 0, self.transaction_delay()
#         ))
#     else:
#         # Randomly choosing a node and starting the mining process
#         self.events.put(MineBlock(
#         node.pid, node.pid, 0, node.get_PoW_delay()
#         ))
# current_event = self.events.get()

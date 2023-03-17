import random
import sys
from copy import deepcopy
from queue import PriorityQueue

import simpy as sp
from treelib import Node, Tree

from block import Block
from event import *
from network import Network


class Simulator:
    def __init__(self, n,zeta,z0,z1, Ttx, I, max_time, simulation_type,print = False):
        if simulation_type == 0:
            self.z0 = z0 # Percentage of slow nodes
        else:
            self.z0 = 50 # Percentage of slow nodes for selfish and stubborn mining
        self.N = Network(n,zeta,self.z0,z1,I,simulation_type,print) # Create the network
        self.z1 = z1 # Percentage of low CPU nodes
        self.Ttx = Ttx # Mean transaction interarrival time
        self.I = I # Mean block interarrival time
        self.txn_id = 0
        self.block_id = 1
        self.num_min_events = 0
        self.zeta = zeta
        self.max_time = max_time
        self.env = sp.Environment()
        self.events = PriorityQueue()
        self.global_transactions = {} # To store th TXN object indexed by the unique ID of the TXN
        self.global_Blocks = {} 
        self.global_Blocks["Block_0"] = Block(0,None,None,0,[],[100]*self.N.num_nodes,0)
        self.print = print
        
    # VERIFIED
    def transaction_delay(self):
        return random.expovariate(1 / self.Ttx)
    
    def run(self):
        for node in self.N.nodes:
            self.env.process(create_transaction(self,node))
            self.env.process(mine_block(self,node))
        self.env.run(until = self.max_time)

    # VERIFIED
    def print_blockchains(self,num = 4,normal = False):
        num = min(num,self.N.num_nodes-1)
        for node in self.N.nodes[0:num]:
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
    S = Simulator(100, 0, 0, 1000, 6, 10000,0)
    S.run()
    S.print_blockchains()
    S.visualize()


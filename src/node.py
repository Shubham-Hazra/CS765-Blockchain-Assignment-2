import collections
import json
import pickle
import random
import sys
from queue import Queue

import matplotlib.pyplot as plt
import networkx as nx
from treelib import Tree

from block import *


class Node:
    def __init__(self, pid, attrb, num_nodes,is_adversary=False,simulation_type=0):
        self.pid = pid  # Unique Id of the peer
        self.cpu = attrb['cpu']  # CPU speed of the peer
        self.hashing_power = attrb['hashing_power']  # Hashing power of the peer
        self.speed = attrb['speed']  # Speed of the peer
        self.I = attrb['I']  # Average interarrival time of the blocks
        self.balance = 100  # Balance of the peer
        self.is_adversary = is_adversary  # True if the peer is an adversary
        self.simulation_type = simulation_type  # 0 for normal, 1 for adversary, 2 for adversary
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.blockchain_tree = {"Block_0": {"parent": None, "time":0}} # Blockchain tree of the peer
        self.blockchain = {"Block_0":Block(0,None,None,0,[],[100]*num_nodes,0)}  # Blockchain of the peer - stores the block objects, Initially the genesis block is added
        self.longest_chain = ["Block_0"] # Longest chain of the peer as a list of block ids
        self.public_max_len = 0  # Length of the longest public chain
        self.private_len = 0  # Length of the private chain
        self.lead = 0  # Lead of the adversary
        self.mining_at_block = Block(0,None,None,0,[],[100]*num_nodes,0)
        self.public_mining_block = Block(0,None,None,0,[],[100]*num_nodes,0)
        self.state_0_dash = False
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.txn_pool = set() # List of all transactions that the peer can include in a block
        self.txn_list = set()  # List of all transactions seen till now by the node
        self.block_buffer = set()  # List of blocks that the peer has heard but not added to its blockchain because parent block is not yet added
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.blocksReceiveTime = []
        #---------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.private_blockchain = [Block(0,None,None,0,[],[100]*num_nodes,0)]
        self.private_blockchain_tree = {"Block_0": {"parent": None, "time":0}}
######################################################################################################################################################
    # Functions for the adversary
    def add_to_private_blockchain(self, simulator, block):
        self.private_blockchain.append(block)
        self.private_blockchain_tree[block.block_id] = {"parent": block.previous_id, "time": simulator.env.now}
        self.add_block(simulator, block)
    
    def get_private_blockchain_len(self):
        return len(self.private_blockchain)
######################################################################################################################################################
    # The following functions will be used to add the block that the node has heard, to its blockchain and remove common TXNs from its TXN pool
     
    # VERIFIED
    # Function to add a block to the blockchain
    def add_block(self,simulator, block):
        if block.block_id in self.blockchain.keys():
            return False

        # Updating the list of transactions that the peer has seen 
        self.update_txn_list(block) 
        
        # Add block to blockchain or in the buffer
        if block.previous_id in self.blockchain.keys(): # Checking if the parent block is already in the blockchain
            if not self.add_block_to_chain(simulator, block): # Return false if validation is wrong
                return False
        else:
            self.block_buffer.add(block) # Adding the block to the block buffer

        # Also check whether there is a block in the buffer whose parent has come in the main blockchain
        to_discard = set()
        sorted_buffer_list = list(self.block_buffer)
        sorted_buffer_list.sort(key=lambda x: int(x.block_id[6:]))
        for block in sorted_buffer_list:
            if block.previous_id in self.blockchain.keys():
                if not self.add_block_to_chain(simulator, block):
                    to_discard.add(block)
                    continue
                to_discard.add(block)
        self.block_buffer = self.block_buffer - to_discard
        return True
    
    # VERIFIED
    # Adds block to the longest chain in the blockchain after validating the TXNs
    def add_block_to_chain(self,simulator, block):
        if self.pid != 0: 
            if self.validate_block(simulator, block): # Checking if the block is valid
                self.blockchain[block.block_id] = block # Adding the block to the blockchain
                self.blockchain_tree[block.block_id] = {"parent": block.previous_id, "time": simulator.env.now} # Adding the block to the blockchain tree
                self.blockchain[block.block_id].length = self.blockchain[block.previous_id].length + 1 # Updating the length of the block
                if self.blockchain[block.block_id].length > self.public_max_len: # Checking if the block is the longest block
                    self.mining_at_block = block
                    self.public_max_len = self.blockchain[block.block_id].length # Updating the length of the longest chain
                    self.longest_chain = self.find_longest_chain() # Updating the longest chain
                    if block.creator_id != 0:
                        self.balance = self.blockchain[block.block_id].balances[self.pid] # Updating the balance of the peer
                    self.update_txn_pool() # Updating the list of transactions that the peer can include in a block
                print(f"{self.pid} says {block.block_id} is valid and added to its blockchain")
                return True
            else:
                print(f"{self.pid} says {block.block_id} is invalid")
                return False
        elif self.pid == 0:
            if self.validate_block(simulator, block):
                self.blockchain[block.block_id] = block # Adding the block to the blockchain
                self.blockchain_tree[block.block_id] = {"parent": block.previous_id, "time": simulator.env.now} # Adding the block to the blockchain tree
                self.blockchain[block.block_id].length = self.blockchain[block.previous_id].length + 1 # Updating the length of the block
                if block.creator_id != 0:
                    self.public_max_len = self.blockchain[block.block_id].length # Updating the length of the longest chain
                    if self.blockchain[block.block_id].length > self.private_len: # Checking if the block is the longest block
                        self.longest_chain = self.find_longest_chain() # Updating the longest chain
                        self.mining_at_block = block
                        self.private_len = self.blockchain[block.block_id].length # Updating the length of the longest private chain
                        self.balance = self.blockchain[block.block_id].balances[self.pid] # Updating the balance of the peer
                        print(f"{self.pid} says {block.block_id} is valid and added to its blockchain")
                    self.lead = self.private_len - self.public_max_len # Updating the lead of the adversary
                    return True
                if self.blockchain[block.block_id].length >= self.public_max_len: # Checking if the block is the longest block
                    self.mining_at_block = block
                    self.longest_chain = self.find_longest_chain() # Updating the longest chain
                self.private_len = self.blockchain[block.block_id].length # Updating the length of the longest private chain
                self.lead = self.private_len - self.public_max_len # Updating the lead of the adversary
                print(f"{self.pid} says {block.block_id} is valid and added to its blockchain")
                return True
            else:
                print(f"{self.pid} says {block.block_id} is invalid")
                return False

    # VERIFIED
    # Function to check if the block is valid
    # Assuming a global transaction list and a global balance list
    # SIMULATOR MAY GENERATE BLOCKS WITH SAME TXNs, BUT RECEIVING NODE WILL NOT VALIDATE
    # This only verifies whether duplicate TXNs are there in the block - validity of TXNs is checked in another function
    def validate_block(self,simulator, block):
        # Find all the TXNs in the longest chain (parent TXNs) and checks whether TXNs match with the TXns in the block - if yes, then reject, else, attach
        parent_txns = self.find_parent_txns(block)
        # Checks whether TXNs in the block are there in the main blockchain
        for txn in block.transactions[:-1]:
            if txn in parent_txns: # Checking if the transaction is already included in the blockchain
                print(self.pid,"says that",txn,"is already there in the chain")
                return False
        
        # Validates the TXNs (balances after the TXN are executed) in the block 
        for txn_id in block.transactions[:-1]:
            txn = simulator.global_transactions[txn_id]
            if block.balances[txn.sender_id]<0: # Checking if the balance of the sender is negative
                print("Balance of",txn.sender_id,"is negative")
                return False

        # If no matching TXNs, (i.e. when it comes out of the loop), then return True
        return True # Assuming that a block is broadcasted only if the balances are non-negative and hence the block is valid

    # VERIFIED
    # Function to find the longest chain in the blockchain
    def find_longest_chain(self):
        longest_chain = []
        max_block_id = "Block_0"
        max_length = 0

        # Find the block with the longest length
        for block_id,block in self.blockchain.items():
            if block.length > max_length: # Finding the block with the maximum length
                max_block_id = block_id
            elif block.length == max_length: # Break ties with lower block number
                if int(block.block_id[6:]) < int(self.blockchain[max_block_id].block_id[6:]):
                    max_block_id = block.block_id
        
        # Update the new blockchain
        while max_block_id != None: # Traversing backwards till the genesis block
            longest_chain.append(max_block_id)
            max_block_id = self.blockchain_tree[max_block_id]["parent"]

        # Return a list representing the longest chain in the format [BLOCK 0 - BLOCK 1 - ----  BLOCK N]
        return longest_chain[::-1]

    # VERIFIED
    # Find all the TXNs in the parent chain of the given block - in which redundancy of TXNs is checked
    def find_parent_txns(self,block):
        txns = []
        parent = block.previous_id
        if parent == None:
            return txns
        while parent != "Block_0":
            if parent in self.blockchain.keys():
                txns.extend(self.blockchain[parent].transactions)
                parent = self.blockchain_tree[parent]["parent"]
        return txns
    
    def update_txn_list(self,block):
        self.txn_list = self.txn_list | set(block.transactions[:-1])

    # VERIFIED
    # Function to update the transaction pool
    # Transaction list and included TXN need to be updated first - which has been done
    def update_txn_pool(self):
        txn_pool = set()
        included_txn = self.find_parent_txns(self.mining_at_block)
        included_txn.extend(self.mining_at_block.transactions[:-1])
        for txn in self.txn_list:
            if txn not in included_txn:
                txn_pool.add(txn)
        self.txn_pool = txn_pool
    
########################################################################################################################################
    # The following function will be used when node is trying to create new block

    # VERIFIED
    # Get TXN from the TXN pool which are not yet included in any block that the node has heard
    def get_TXN_to_include(self):
        self.update_txn_pool()
        # Return false if TXN pool is empty
        if not self.txn_pool:
            # print("NO TXNs to include")
            return []
        # Choose a random number of TXN between [1,min(999, size of TXN pool)]
        if len(self.txn_pool) > 999:
            upper_limit = 999 # Upper limit is 999 + mining fee TXN + empty block (1 KB) + rest TXNs (999 KB)
        else:
            upper_limit = len(self.txn_pool)
        num_txn_to_mine = random.randint(int(upper_limit*0.9),upper_limit) # Number of transactions to be included in the block
        txn_to_mine = random.sample(list(self.txn_pool),num_txn_to_mine) # Transactions to be included in the block
        return txn_to_mine

    # VERIFIED
    # Mining time of the block
    def get_PoW_delay(self):
        return random.expovariate(self.hashing_power/self.I) 

    # VERIFIED
    # Balances included in the block will be updated at the time of creation of the block
    # If the TXns are invalid, then the balances of at least one node will be negative 
    # Other nodes will check the balances and 
    def update_balances(self,simulator,block):
        # Updating the normal TXNs balances
        for txn_id in block.transactions[:-1]:
            txn = simulator.global_transactions[txn_id]
            block.balances[txn.sender_id]-=txn.amount
            block.balances[txn.receiver_id]+=txn.amount
        
        # Updating the mining fee TXN balance
        block.balances[int(self.pid)]+=50
        return block

#########################################################################################################################################
    # Following function will be used at the end to print the blockchain (tree form) of the node
    
    # VERIFIED
    def print_blockchain(self):
        dict_ = self.blockchain_tree.copy()
        G = nx.Graph()
        for key, value in dict_.items():
            if value['parent'] is not None:
                G.add_node(key)
                G.add_edge(key, value['parent'])
            else:
                G.add_node(key)

        # Print the graph
        color_map = []
        for node in G:
            if self.blockchain[node].creator_id == 0:
                color_map.append('red')
            else: 
                color_map.append('green')     
        plt.figure(figsize=(10, 10))
        nx.draw(G, node_color=color_map, with_labels=True)
        plt.show()


#############################################################################################################################
    def dump_blockchain_tree(self): # Dumping the blockchain tree object
        filename = "blockchain_tree/"+str(self.pid)+".txt"
        sys.stdout = open(filename, 'w')
        tree = Tree()
        tree.create_node("Block_0_0", "Block_0_0")
        for block in self.blockchain_tree.keys():
            if block == "Block_0":
                continue
            tree.create_node(block+"_"+str(self.blockchain_tree[block]["time"]),block+"_"+str(self.blockchain_tree[block]["time"]), parent = self.blockchain_tree[block]['parent']+"_"+str(self.blockchain_tree[self.blockchain_tree[block]['parent']]["time"]))
        tree.show()

    def dump_networkx_graph(self): # Dumping the networkx graph object
        filename = "networkx_graph/"+str(self.pid)+".png"
        G = nx.Graph()
        for key, value in self.blockchain_tree.items():
            if value['parent'] is not None:
                G.add_node(key)
                G.add_edge(key, value['parent'])
            else:
                G.add_node(key)
        plt.figure(figsize=(10, 10))
        nx.draw(G, with_labels=True)
        plt.savefig(filename, format="PNG")
        plt.close()
        
    def dump_blockchain_tree_dict(self): # Dumping the blockchain tree dictionary object
        filename = "blockchain_tree_dict/"+str(self.pid)+".txt"
        with open(filename, 'wb') as f:
            f.write(json.dumps(self.blockchain_tree).encode('utf-8'))
#############################################################################################################################

# Testing the code
if __name__ == "__main__":
    N = Node(1, {"cpu": "low", "speed": "high","hashing_power" : 0.1, "I":0.3},100)
    N.add_block(Block(1, "Block_0", 0, ["txn_1", "txn_2"],[100,100],1,0))
    N.add_block(Block(2, "Block_0", 1,["txn_3", "txn_4"],[100,100],2,0))
    N.add_block(Block(3, "Block_1", 2,  ["txn_5", "txn_6"],[100,100],3,0))
    print(N.blockchain_tree)
    print(N.find_longest_chain())
    print(f"Maximum length: {N.public_max_len}")
    print(N.included_txn)
    print(N.txn_list)
    N.add_txn("txn_3")



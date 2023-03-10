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
    def __init__(self, pid, attrb, num_nodes, isAdversary):

        self.pid = pid  # Unique Id of the peer
        self.cpu = attrb['cpu']  # CPU speed of the peer
        self.hashing_power = attrb['hashing_power']  # Hashing power of the peer
        self.speed = attrb['speed']  # Speed of the peer
        self.I = attrb['I']  # Average interarrival time of the blocks
        self.blockchain_tree = {"Block_0": {"parent": None, "time":0}} # Blockchain tree of the peer
        self.blockchain = {"Block_0":Block(None,None,None,None,0,[100]*num_nodes,0,0)}  # Blockchain of the peer - stores the block objects, Initially the genesis block is added
        self.longest_chain = ["Block_0"] # Longest chain of the peer as a list of block ids
        self.max_len = 0  # Length of the longest chain
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.txn_pool = set() # List of all transactions that the peer can include in a block
        self.txn_list = set()  # List of all transactions seen till now by the node
        self.included_txn = set()  # List of transactions that the peer has included in the longest chain
        self.block_buffer = set()  # List of blocks that the peer has heard but not added to its blockchain because parent block is not yet added
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.blocksReceiveTime = []
        #---------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.private_blockchain = []
        self.private_blockchain_tree = {}
        self.isAdversary = isAdversary # IsAdvsersary = 1 means selfish mining and isAdversary = 2 is stubborn  mining
######################################################################################################################################################
    # Functions for the adversary
    def add_to_private_blockchain(self, simulator, block):
        self.private_blockchain.append(block)
        self.private_blockchain_tree[block.block_id] = {"parent": block.previous_id, "time": simulator.curr_time}
        self.add_block(simulator, block)
    
    def release_from_private_chain(self):
        block_to_remove = self.private_blockchain.pop(0)
        del self.private_blockchain_tree[block_to_remove.block_id]
        return block_to_remove
    
    def get_private_blockchain_len(self):
        return len(self.private_blockchain)
######################################################################################################################################################
    # The following functions will be used to add the block that the node has heard, to its blockchain and remove common TXNs from its TXN pool
     
    # VERIFIED
    # Function to add a block to the blockchain
    def add_block(self,simulator, block):
        if block.block_id in self.blockchain.keys():
            return False
        # Extracting the non-mining fee TXNs
        block.trasactions = block.transactions[:-1]

        # Updating the list of transactions that the peer has seen 
        self.update_txn_list(block) 
        
        # Add block to blockchain or in the buffer
        if block.previous_id in self.blockchain.keys(): # Checking if the parent block is already in the blockchain
            if not self.add_block_to_chain(simulator, block): # Return false if validation is wrong
                return False
        elif block.previous_id not in self.block_buffer:
            self.block_buffer.add(block) # Adding the block to the block buffer

        # Also check whether there is a block in the buffer whose parent has come in the main blockchain
        to_discard = set()
        for block in self.block_buffer:
            if block.previous_id in self.blockchain.keys():
                if not self.add_block_to_chain(simulator, block):
                    return False
                to_discard.add(block)
        self.block_buffer = self.block_buffer - to_discard
        return True
    
    # VERIFIED
    # Adds block to the longest chain in the blockchain after validating the TXNs
    def add_block_to_chain(self,simulator, block):
        if self.validate_block(simulator, block): # Checking if the block is valid
            self.blockchain[block.block_id] = block # Adding the block to the blockchain
            self.blockchain_tree[block.block_id] = {"parent": block.previous_id, "time": simulator.curr_time} # Adding the block to the blockchain tree
            self.blockchain[block.block_id].length = self.blockchain[block.previous_id].length + 1 # Updating the length of the block
            if self.blockchain[block.block_id].length > self.max_len: # Checking if the block is the longest block
                self.max_len = self.blockchain[block.block_id].length # Updating the length of the longest chain
                self.longest_chain = self.find_longest_chain() # Updating the longest chain
                self.update_included_txn() # Updating the list of transactions that the peer has included in the longest chain
                self.update_txn_pool() # Updating the list of transactions that the peer can include in a block
            print(f"{self.pid} says {block.block_id} is valid and added to its blockchain")
            print("HELLO")
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
        for txn in block.transactions:
            if txn in parent_txns: # Checking if the transaction is already included in the blockchain
                print(self.pid,"says that",txn,"is already there in the chain")
                return False
        
        # Validates the TXNs (balances after the TXN are executed) in the block 
        for txn_id in block.transactions[:-1]:
            txn = simulator.global_transactions[txn_id]
            if block.balances[txn.sender_id]<0:
                print(self.pid,"says that",block.block_id,"has invalid TXNs")
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
        while parent != "Block_0":
            if parent in self.blockchain.keys():
                txns.extend(self.blockchain[parent].transactions)
                parent = self.blockchain_tree[parent]["parent"]
        return txns

    # VERIFIED
    # Function to update the list of transactions included in the longest chain
    def update_included_txn(self):
        self.included_txn = set()
        for block_id in self.longest_chain:
            if block_id == "Block_0":
                continue        
            self.included_txn = self.included_txn|set(self.blockchain[block_id].transactions)
    
    def update_txn_list(self,block):
        self.txn_list = self.txn_list|set(block.transactions)
        to_discard = set()
        for txn in self.txn_list:
            if int(txn[4:]) < 0:
                to_discard.add(txn)
        self.txn_list-=to_discard


    # VERIFIED
    # Function to update the transaction pool
    # Transaction list and included TXN need to be updated first - which has been done
    def update_txn_pool(self):
        txn_pool = set()
        for txn in self.txn_list:
            if txn not in self.included_txn:
                txn_pool.add(txn)
        self.txn_pool = txn_pool

########################################################################################################################################
    # The following function will be used at the time of creating and forwarding TXNs

    # VERIFIED
    # Adding a transaction to the list of transactions
    def add_txn(self, txn_id):  
        if txn_id not in self.txn_list:
            self.txn_list.add(txn_id)
            self.txn_pool.add(txn_id)
        else:
            print(f"{self.pid} says {txn_id} is already in the list of transactions")

########################################################################################################################################
    # The following function will be used when node is trying to create new block

    # VERIFIED
    # Get TXN from the TXN pool which are not yet included in any block that the node has heard
    def get_TXN_to_include(self):
        print("TXN POOL:",self.txn_pool)

        # Return false if TXN pool is empty
        if not self.txn_pool:
            print("NO TXNs to include")
            return False
        
        # Choose a random number of TXN between [1,min(999, size of TXN pool)]
        if len(self.txn_pool) > 999:
            upper_limit = 999 # Upper limit is 999 + mining fee TXN + empty block (1 KB) + rest TXNs (999 KB)
        else:
            upper_limit = len(self.txn_pool)
        num_txn_to_mine = random.randint(1,upper_limit) # Number of transactions to be included in the block
        txn_to_mine = random.sample(self.txn_list,num_txn_to_mine) # Transactions to be included in the block
        print("TXN to include: ",num_txn_to_mine)
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
        print(block.transactions)
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
    N.add_block(Block(1, "Block_0", 0, ["txn_1", "txn_2"],14,[100,100],1,0))
    N.add_block(Block(2, "Block_0", 1,["txn_3", "txn_4"],14,[100,100],2,0))
    N.add_block(Block(3, "Block_1", 2,  ["txn_5", "txn_6"],14,[100,100],3,0))
    print(N.blockchain_tree)
    print(N.find_longest_chain())
    print(f"Maximum length: {N.max_len}")
    print(N.included_txn)
    print(N.txn_list)
    N.add_txn("txn_3")



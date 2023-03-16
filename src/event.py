import random
import sys
import time
from copy import deepcopy

import simpy as sp

from block import Block
from network import Network
from transaction import Transaction

VALID_RATIO = 0.03

def create_transaction(simulator,node):
    while True:
        txn_gen_delay = simulator.transaction_delay()
        env = simulator.env
        yield env.timeout(txn_gen_delay)
        random_node = random.randint(0, simulator.N.num_nodes - 1)
        while (random_node == node.pid):
            random_node = random.randint(0, simulator.N.num_nodes - 1)
        txn_delay = simulator.transaction_delay()
        amount = node.balance * VALID_RATIO
        node.balance -= amount
        yield env.timeout(txn_delay)
        txn = Transaction(simulator.txn_id, node.pid, random_node, amount, False)
        simulator.txn_id += 1
        simulator.global_transactions[txn.txn_id] = txn
        txn_set = set()
        txn_set.add(txn.txn_id)
        node.txn_list = node.txn_list | txn_set
        receive_list = [False]*simulator.N.num_nodes
        receive_list[node.pid] = True
        forward_transactions(simulator,txn,node,receive_list)
        # print("Node {} created {} transaction at time {}".format(node.pid,txn.txn_id, env.now))

def forward_transactions(simulator,txn,node,received_list):
    env = simulator.env
    neighbors = simulator.N.G.neighbors(node.pid)
    for neighbor in neighbors:
        if received_list[neighbor] == True:
            continue
        latency = simulator.N.get_latency(node.pid,neighbor,0.001)
        received_list[neighbor] = True
        env.process(receive_transactions(simulator,txn,simulator.N.nodes[neighbor],latency,received_list))

def receive_transactions(simulator,txn,node,latency,received_list):
    env = simulator.env
    yield env.timeout(latency)
    txn_set = set()
    txn_set.add(txn.txn_id)
    node.txn_list = node.txn_list | txn_set
    # print("Node {} received {} at time {}".format(node.pid,txn.txn_id,env.now))
    forward_transactions(simulator,txn,node,received_list)

def mine_block(simulator,node):
    env = simulator.env
    while True:
        pow_time = node.get_PoW_delay()
        txns_to_include = node.get_TXN_to_include()
        coinbase_txn = Transaction(simulator.txn_id,node.pid,node.pid,50,True)
        txns_to_include.append(coinbase_txn.txn_id)
        simulator.global_transactions[coinbase_txn.txn_id] = coinbase_txn
        simulator.txn_id += 1
        if node.is_adversary == False:
            if (len(txns_to_include) < 2):
                yield env.timeout(pow_time)
                print("-------------------------------------------------------------------------------------------------")
                print("Node {} did not have any TXNs to include at time {}".format(node.pid,env.now))
                continue
            prev_block = node.mining_at_block
            balances = deepcopy(prev_block.balances)
            yield env.timeout(pow_time)
            if (node.mining_at_block.block_id == prev_block.block_id):
                print("-------------------------------------------------------------------------------------------------")
                block = Block(simulator.block_id,node.pid,prev_block.block_id,env.now,txns_to_include,balances,prev_block.length+1)
                print("Node {} mined {} at time {}".format(node.pid,block.block_id,env.now))
                node.update_balances(simulator,block)
                simulator.block_id += 1
                valid = node.add_block(simulator,block)
                if valid == False:
                    continue
                node.blocksReceiveTime.append(f"{block.block_id}_{env.now}")
                simulator.global_Blocks[block.block_id] = block
                received_list = [False]*simulator.N.num_nodes 
                received_list[node.pid] = True
                forward_block(simulator,block,node,received_list)
            else:
                print("-------------------------------------------------------------------------------------------------")
                print("Another node mined a block before node {} at time {}".format(node.pid,env.now))
            print("-------------------------------------------------------------------------------------------------")
        else:
            yield env.timeout(pow_time)
            prev_block = node.mining_at_block
            balances = deepcopy(prev_block.balances)
            block = Block(simulator.block_id,node.pid,prev_block.block_id,env.now,[],balances,prev_block.length+1)
            print("Node {} mined {} at time {}".format(node.pid,block.block_id,env.now))
            simulator.block_id += 1
            node.add_to_private_blockchain(simulator,block)
            node.blocksReceiveTime.append(f"{block.block_id}_{env.now}")
            simulator.global_Blocks[block.block_id] = block
            if node.state_0_dash == True:
                    print(f"Released {block.block_id} Immediately at time {env.now} with lead {node.lead} and length {block.length}")
                    received_list = [False]*simulator.N.num_nodes 
                    received_list[node.pid] = True
                    node.private_blockchain.pop(0)
                    forward_block(simulator,block,node,received_list)
                    node.state_0_dash = False
                    node.lead = 0


def forward_block(simulator,block,node,received_list):
    env = simulator.env
    neighbors = simulator.N.G.neighbors(node.pid)
    for neighbor in neighbors:
        if received_list[neighbor] == True:
            continue
        latency = simulator.N.get_latency(node.pid,neighbor,block.get_size())
        received_list[neighbor] = True
        env.process(receive_block(simulator,block,simulator.N.nodes[neighbor],latency,received_list))

def receive_block(simulator,block,node,latency,received_list):
    env = simulator.env
    yield env.timeout(latency)
    print("-------------------------------------------------------------------------------------------------")
    print("Node {} received block {} at time {}".format(node.pid,block.block_id,env.now))
    added = node.add_block(simulator,block)
    node.blocksReceiveTime.append(f"{block.block_id}: {env.now}")
    print("-------------------------------------------------------------------------------------------------")
    if node.is_adversary == False:
        if added:
            forward_block(simulator,block,node,received_list)
        else:
            print("-------------------------------------------------------------------------------------------------")
            print("Node {} received an invalid block {} at time {}".format(node.pid,block.block_id,env.now))
            print("-------------------------------------------------------------------------------------------------")  

    else:
        if node.simulation_type == 1: 
            if node.lead == 0 and len(node.private_blockchain) > 0:
                print(len(node.private_blockchain))
                adv_block = node.private_blockchain.pop(0)
                print("Reached 0' state after making block {} at time {}".format(adv_block.block_id,env.now))
                print("Reached 0' state after receiving block {} at time {}".format(block.block_id,env.now))
                node.state_0_dash = True
                received_list = [False]*simulator.N.num_nodes 
                received_list[node.pid] = True
                forward_block(simulator,adv_block,node,received_list)
                node.private_blockchain = []
                node.lead = 0
            elif node.lead == 1:
                for adv_block in node.private_blockchain:
                    received_list = [False]*simulator.N.num_nodes 
                    received_list[node.pid] = True
                    forward_block(simulator,adv_block,node,received_list)
                node.private_blockchain = []
                node.lead = 0
            elif node.lead > 1:
                adv_block = node.private_blockchain.pop(0)
                received_list = [False]*simulator.N.num_nodes
                received_list[node.pid] = True
                forward_block(simulator,adv_block,node,received_list)
        elif node.simulation_type == 2:
            pass

    

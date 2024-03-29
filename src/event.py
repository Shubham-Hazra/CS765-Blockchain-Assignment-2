import random
import sys
import time
from copy import deepcopy

import simpy
import simpy as sp

from block import Block
from network import Network
from transaction import Transaction

VALID_RATIO = 0.03

def create_transaction(simulator,node):
    env = simulator.env
    while True:
        if env.now > simulator.max_time:
            return
        txn_gen_delay = simulator.transaction_delay()
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
    forward_transactions(simulator,txn,node,received_list)

def mine_block(simulator,node):
    env = simulator.env
    while True:
        if simulator.print:
            print("-------------------------------------------------------------------------------------------------")
            print("Started mining at Node" , node.pid)
            print("-------------------------------------------------------------------------------------------------")
        pow_time = node.get_PoW_delay()
        txns_to_include = node.get_TXN_to_include()
        coinbase_txn = Transaction(simulator.txn_id,node.pid,node.pid,50,True)
        txns_to_include.append(coinbase_txn.txn_id)
        simulator.global_transactions[coinbase_txn.txn_id] = coinbase_txn
        simulator.txn_id += 1
        if node.is_adversary == False:
            if (len(txns_to_include) < 2):
                try:
                    yield env.timeout(pow_time)
                except simpy.Interrupt as i:
                    if simulator.print:
                        print("-------------------------------------------------------------------------------------------------")
                        print(i.cause)
                        print("-------------------------------------------------------------------------------------------------")
                    continue # Restart the mining process again
                if simulator.print:
                    print("-------------------------------------------------------------------------------------------------")
                    print("Node {} did not have any TXNs to include at time {}".format(node.pid,env.now))
                continue
            prev_block = node.mining_at_block
            balances = deepcopy(prev_block.balances)
            try:
                yield env.timeout(pow_time)
            except simpy.Interrupt as i:
                if simulator.print:
                        print("-------------------------------------------------------------------------------------------------")
                        print(i.cause)
                        print("-------------------------------------------------------------------------------------------------")
                continue # Restart the mining process again
            if env.now > simulator.max_time:
                return
            block = Block(simulator.block_id,node.pid,prev_block.block_id,env.now,txns_to_include,balances,prev_block.length+1)
            if simulator.print:
                print("-------------------------------------------------------------------------------------------------")
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
            if simulator.print:
                print("-------------------------------------------------------------------------------------------------")
        elif node.simulation_type == 1:
            prev_block = node.mining_at_block
            try:
                yield env.timeout(pow_time)
            except simpy.Interrupt as i:
                if simulator.print:
                        print("-------------------------------------------------------------------------------------------------")
                        print(i.cause)
                        print("-------------------------------------------------------------------------------------------------")
                continue # Restart the mining process again
            if env.now > simulator.max_time:
                return
            if (node.mining_at_block.block_id != prev_block.block_id):
                continue
            balances = deepcopy(prev_block.balances)
            block = Block(simulator.block_id,node.pid,prev_block.block_id,env.now,[],balances,prev_block.length+1)
            if simulator.print:
                print("Node {} mined {} at time {}".format(node.pid,block.block_id,env.now))
            simulator.block_id += 1
            node.add_to_private_blockchain(simulator,block)
            node.blocksReceiveTime.append(f"{block.block_id}_{env.now}")
            simulator.global_Blocks[block.block_id] = block
            if node.state_0_dash == True:
                    if simulator.print:
                        print(f"Released {block.block_id} Immediately at time {env.now} with lead {node.lead} and length {block.length}")
                    received_list = [False]*simulator.N.num_nodes 
                    received_list[node.pid] = True
                    node.private_blockchain.pop(0)
                    forward_block(simulator,block,node,received_list)
                    node.state_0_dash = False
                    node.lead = 0
        elif node.simulation_type == 2:
            prev_block = node.mining_at_block
            try:
                yield env.timeout(pow_time)
            except simpy.Interrupt as i:
                if simulator.print:
                        print("-------------------------------------------------------------------------------------------------")
                        print(i.cause)
                        print("-------------------------------------------------------------------------------------------------")
                continue # Restart the mining process again
            if env.now > simulator.max_time:
                return
            if (node.mining_at_block.block_id != prev_block.block_id):
                continue
            prev_block = node.mining_at_block
            balances = deepcopy(prev_block.balances)
            block = Block(simulator.block_id,node.pid,prev_block.block_id,env.now,[],balances,prev_block.length+1)
            if simulator.print:
                print("Node {} mined {} at time {}".format(node.pid,block.block_id,env.now))
            simulator.block_id += 1
            node.add_to_private_blockchain(simulator,block)
            node.blocksReceiveTime.append(f"{block.block_id}_{env.now}")
            simulator.global_Blocks[block.block_id] = block
            if node.state_0_dash == True:
                    if simulator.print:
                        print(f"Transitioning to lead {node.lead} at time {env.now} with length {block.length}")
                    node.state_0_dash = False
                    node.lead = 1


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
    if simulator.print:
        print("-------------------------------------------------------------------------------------------------")
        print("Node {} received block {} at time {}".format(node.pid,block.block_id,env.now))
    prev_mining_at = node.mining_at_block.block_id # The block on  which the node was previously mining at
    added = node.add_block(simulator,block)
    if env.now > simulator.max_time:
        forward_block(simulator,block,node,received_list)
        return
    node.blocksReceiveTime.append(f"{block.block_id}: {env.now}")
    node.state_0_dash = False
    if simulator.print:
        print("-------------------------------------------------------------------------------------------------")
    if added:
            # Checks whether the block on which the node was mining has changed or not
            if (node.mining_at_block.block_id != prev_mining_at):
                # Restart the mining process
                simulator.node_process[node.pid].interrupt(f"Node {node.pid} restarted mining at time {env.now}")
                # While loop at another node automatically restarts mining
    if node.is_adversary == False:
        if added:
            forward_block(simulator,block,node,received_list)
        else:
            if simulator.print:
                print("-------------------------------------------------------------------------------------------------")
                print("Node {} received an invalid block {} at time {}".format(node.pid,block.block_id,env.now))
                print("-------------------------------------------------------------------------------------------------")  
    else:
        if node.simulation_type == 1: 
            if node.lead == 0 and len(node.private_blockchain) > 0:
                adv_block = node.private_blockchain.pop(0)
                if simulator.print:
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
            if node.lead == 0 and len(node.private_blockchain) > 0:
                adv_block = node.private_blockchain.pop(0)
                if simulator.print:
                    print("Reached 0' state after making block {} at time {}".format(adv_block.block_id,env.now))
                    print("Reached 0' state after receiving block {} at time {}".format(block.block_id,env.now))
                node.state_0_dash = True
                received_list = [False]*simulator.N.num_nodes 
                received_list[node.pid] = True
                forward_block(simulator,adv_block,node,received_list)
                node.private_blockchain = []
                node.lead = 0
            elif node.lead >= 1:
                adv_block = node.private_blockchain.pop(0)
                received_list = [False]*simulator.N.num_nodes 
                received_list[node.pid] = True
                forward_block(simulator,adv_block,node,received_list)

    

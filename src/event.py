import random
import sys
import time
from copy import deepcopy

from block import Block
from network import Network
from transaction import Transaction


class Event(object):

    # VERIFIED
    def __init__(self, node_id, creator_id, create_time, run_time):
        super(Event, self).__init__()
        self.node_id = node_id
        self.creator_id = creator_id
        self.create_time = create_time
        self.run_time = run_time 

    # VERIFIED
    def print_run_time(self):
        print(self.run_time)

    # VERIFIED
    def __lt__(self, non_self):
        # To define a < operator to put into the Priority Queue
        return self.run_time < non_self.run_time
    
    # VERIFIED
    # Function for printing message information
    def print(self):
        print("Event from " + str(self.creator_id) + " at time " + str(self.run_time) + " running on node", str(self.node_id))

# VERIFIED
class CreateTXN(Event):
    # VERIFIED
    def __init__(self, node_id, creator_id, create_time, run_time): # N is the network for extracting peer information
        super(CreateTXN, self).__init__(node_id, creator_id, create_time, run_time) # Inherits the Event class - whenever CreateTXN object is created, Event (parent) class is initialized

    # VERIFIED
    def addEvent(self, N, simulator) :  
        # self.print_run_time()
        current = N.nodes[self.node_id]

        # Creates a TXN setting:
        # 1. Randomly select a receiver
        receiver = list(set(N.nodes) - set([current]))
        receiver = random.choice(receiver)

        # 2. randomly generate TXN amount 
        TXN_amount = 10 * random.uniform(0, 1) # Some probability that the TXN generated is inavlid

        # 3.1 Does not check whether the TXN is invalid, just broadcasts, TXn will be validated at the time of creation of the block
        new_txn = Transaction(simulator.txn_id, self.node_id, receiver.pid,TXN_amount, len(N.nodes))
        simulator.txn_id += 1

        # 3.2 Add the  TXN to the simulator global list
        simulator.global_transactions[new_txn.id] = new_txn

        # For debugging
        print("TXN Gen:", self.node_id ,"heard that ", end= " ")
        new_txn.print_transaction()

        # 3.3 Since this node has itself created the TXN, flip its value to 1 in the boolean array
        new_txn.received[self.node_id] = 1

        # 4. Add the TXN id to the TXN pool of the creator
        current.add_txn(new_txn.id)

        # 5. adds the ReceiveTXN Event in the Queue for those peers who have not yet received the TXN (ensured through a Boolean array associated with the Event)
        for neighbor in N.G.neighbors(self.node_id):
            t = N.get_latency(self.node_id, neighbor, .008) # TXN is 8000 bits = 1KB = .008MB
            new_txn.received[neighbor] = 1
            simulator.events.put(ReceiveTXN(
                new_txn,
                neighbor,
                self.node_id,
                self.run_time,
                self.run_time + t
            ))
        
        # OPTIONAL: SPAWN ANOTHER CREATE TXN EVENT AFTER THE CURRENT ONE - JUST SO THAT THE QUEUE DOES NOT BECOME EMPTY
        if random.random()>0.6:
            simulator.events.put(CreateTXN(
                self.node_id,
                self.node_id,
                self.run_time,
                self.run_time + simulator.transaction_delay()
            ))

 # VERIFIED
class ReceiveTXN(Event):
    # VERIFIED
    # NOTE: THE creator_id is creator of the EVENT, NOT the TXN
    def __init__(self, transaction, node_id, creator_id, create_time, run_time):
        super(ReceiveTXN, self).__init__(node_id, creator_id, create_time, run_time)
        self.transaction = transaction

    # VERIFIED
    def addEvent(self, N, simulator):
        # Create object of the current node
        # self.print_run_time()
        current = N.nodes[self.node_id]

        # For debugging
        print("TXN Fwd:", self.node_id, "heard that ", end = " ")
        self.transaction.print_transaction()

        # Add the TXN id to the TXN pool of the creator
        current.add_txn(self.transaction.id)

        # 4. adds the ReceiveTXN Event in the Queue for those peers who have not yet received the TXN (ensured through a Boolean array associated with the Event)
        for neighbor in N.G.neighbors(self.node_id):

            if self.transaction.received[neighbor] == 0:

                t = N.get_latency(self.node_id, neighbor, .008) # TXN is 8000 bits = 1KB = .008MB
                self.transaction.received[neighbor] = 1
                simulator.events.put(ReceiveTXN(
                    self.transaction,
                    neighbor,
                    self.node_id,
                    self.run_time,
                    self.run_time + t
                ))
# VERIFIED
class ForwardBlock(Event):
    # VERIFIED
    def __init__(self, block, node_id, creator_id, creat_time, run_time):
        super(ForwardBlock, self).__init__(node_id, creator_id, creat_time, run_time)
        self.block = block
    # VERIFIED
    def addEvent(self, N, simulator): 
        # self.print_run_time()
        current = N.nodes[self.node_id]

        # Stores the chain length before adding the block to the chain
        chain_length_before_adding = current.max_len

        # Do nothing if the block has already been seen
        if not self.block.block_id in current.blockchain.keys():
            # Add the block to the blockchain of the node and remove common TXNs from the TXN pool of the node
            # OR Add the block to the buffer
            # Make a copy of the block 
            # received_block = deepcopy(self.block)

            # The following events take place on hearing a TXN
            # 1. Update the TXN list seen 
            # 2. Add the block to blockchain in parent chain - if parent is present, else add it to the buffer
            # 3. Update the cache - check whether there is a block in buffer whose parent has arrived 
            if not current.add_block(simulator, self.block):
                print("BLOCK ERROR on",current.pid,": ERROR IN ADDING BLOCK DUE TO VALIDATION")
                # print("ERRANEOUS BLOCK")
                # self.block.print_block()
                return False
            self.block.print_block()
            # print(current.blockchain)
            # print(current.add_block(simulator, self.block))
            # print(current.blockchain)
            # sys.exit(0)


            # Now, the following 3 things can happen:
            #.1. block ends up in the buffer
            # 2. block is in blockchain and longest chain length increases
            # 3. block is in blockchain and longest chain length remains the same

            #.1. block ends up in the buffer - do not forward
            if self.block in current.block_buffer:
                print("BLOCK IS IN BUFFER. PARENT HAS NOT ARRIVED")
                return 
            # Else forward            

            # To store the arrival time of the block received, between t_k and t_k + T_k, during PoW, to ensure that no other block had come between t_k and t_k + T_k - so that the node can create a block
            # Append information about chain length BEFORE adding the new block in the blockchain
            current.blocksReceiveTime.append([self.run_time,chain_length_before_adding]) # To store the execution time of the event so that we can ensure no block has arrived between t_k and T_k

            print("previous ID of the block is",self.block.previous_id)
            #######################################################################################################################################
            # After the block receives the Block from its peers and the length of the longest chain is increased, The node starts the PoW again - See last paragraph of the Problem statement 7th statement
            #######################################################################################################################################
            chain_length_after_adding = current.max_len
            print("CHAIN LENGTH BEFORE ADDING:", chain_length_before_adding)
            print("CHAIN LENGTH AFTER ADDING:", chain_length_after_adding)
            #---------------------------------------------------------------------------------------------------------------------------------------
            if chain_length_after_adding > chain_length_before_adding:
                # Create a block and add mining event
                PoW_delay = current.get_PoW_delay()

                # Traverse the longest chain and find all transactions that've been spent
                last_blck = current.longest_chain[-1]# Stores the id of the block which is being mined in the blockchain of that node
                
                # Get TXn to be included in the block (all the maximum limits and other conditions are handled by the node)
                # To terminate the block mining process if the node has no TXNs to include in the block
                if not current.txn_pool:
                    print("MINING UNSUCCESSFUL: No TXN to include")
                    return 

                txn_to_include = current.get_TXN_to_include()

                # To terminate the block mining process if the node has no TXNs to include in the block        
                if not txn_to_include:
                    print("MINING UNSUCCESSFUL: No TXN to include")
                    return

                # Get the balances of the last block in the blockchain
                prev_block_balances = N.nodes[self.node_id].blockchain[last_blck].balances
                # Generate a new block
                if current.pid == 0:
                    # Create a selfish block
                    selfish_block = Block(current.pid,self.block.block_id, self.run_time + PoW_delay, [],N.num_nodes,[100]+[0]*(N.num_nodes-1), simulator.block_id, len(current.longest_chain))
                    # if (current.lead == 1 and block
##############################################################################################################################################################################################
                new_blk = Block(current.pid,self.block.block_id, self.run_time + PoW_delay, txn_to_include,N.num_nodes,deepcopy(prev_block_balances), simulator.block_id, len(current.longest_chain))
                # Update the balances when the block is actually created - MineBlock Event

                # For debugging
                print("BLOCK ID:",new_blk.block_id,", PREVIOUS POINTER:",new_blk.previous_id)
                simulator.block_id += 1

                print("STARTING POW on",self.node_id)
                print("PoW delay for", self.node_id,"is",PoW_delay)
                simulator.events.put(MineBlock( ################ THIS CORRESPONDS TO TIME t_k - the TIME FROM WHICH THE NODE WAITS TO CHECK WHETHER ANY OTHER BLCK RRIVES OR NOT (for T_k time)
                    new_blk,
                    self.node_id,
                    self.node_id,
                    self.run_time,
                    self.run_time + PoW_delay # Updated block_delay() as described in simulating PoW section
                ))
            else:
                print("CONTINUING PoW: Length of longest chain same after adding the block")

            #-------------------------------------------------------------------------------------------------------------------------------------------
            # Forawrd the block received anyways
            # Forwarding the block to its peers only if the current block is not stored in the nodes cache - because its parent has not arrived yet
            for neighbor in N.G.neighbors(self.node_id):

                # Exclude the creator of the block
                if neighbor != self.block.creator_id and self.block.received[neighbor] == 0:

                    t = N.get_latency(self.node_id, neighbor, self.block.get_size()) # To calculate the latency of the block based on the number of transactions in the block
                    self.block.received[neighbor] = 1 # That the node has seen the block
                    simulator.events.put(ForwardBlock(
                        self.block,
                        neighbor,
                        self.node_id,
                        self.run_time,
                        self.run_time + t
                    ))
        else:
            print("ONLY FORWARDING BLOCK on",self.node_id,":",self.node_id,"has already added",self.block.block_id,"into his blockchain")

            # No need to check whether parent of the block is present in the blockhain - because block is only added if parent is there in blockchain
            # Program only comes here if the block is already in the blockchain
            # Forwarding the block to its peers only if the current block is not stored in the nodes cache - because its parent has not arrived yet
            for neighbor in N.G.neighbors(self.node_id):

                # Exclude the creator of the block
                if neighbor != self.block.creator_id and self.block.received[neighbor] == 0:

                    t = N.get_latency(self.node_id, neighbor, self.block.get_size()) # To calculate the latency of the block based on the number of transactions in the block
                    self.block.received[neighbor] = 1 # That the node has seen the block
                    simulator.events.put(ForwardBlock(
                        self.block,
                        neighbor,
                        self.node_id,
                        self.run_time,
                        self.run_time + t
                    ))
# VERIFIED
class MineBlock(Event):
    # VERIFIED
    def __init__(self,block, node_id, creator_id, create_time, run_time):
        super(MineBlock, self).__init__(node_id, creator_id, create_time, run_time)
        self.block = block

    def addEvent(self, N, simulator):
        # self.print_run_time()
        current = N.nodes[self.node_id]
        if self.node_id == 0:
            # last_blck = current.longest_chain[-1]# Stores the id of the block which is being mined in the blockchain of that node
            # new_private_blk = Block(current.pid,N.nodes[self.node_id].blockchain[last_blck].block_id, self.block.created_at, [],N.num_nodes,[100]+[0]*(simulator.N.num_nodes-1), simulator.block_id, len(current.longest_chain))
            current.add_to_private_blockchain(simulator, self.block) # Adds to private blockchain
            print("MINING SUCCESSFUL FOR SELFISH MINER: NEW BLOCK GENERATED")
            return
        
        
        # The block generation event was created at t_k (create_time) and scheduled for t_k + T_k (run_time) 
        # if there is some block in the list of blocks seen by the node such that it reached that node at timet,t_k < t < t_k + T_k then reject this block generation event
        for block_rcv_time, length in current.blocksReceiveTime: 
            if block_rcv_time > self.create_time and block_rcv_time < self.run_time and length < current.max_len:
                print("MINING UNSUCCESSFUL: PoW on",self.node_id,"Unsuccessful :(, some other node has created the block")
                return

        ## MINING SUCCESSFUL !! - ADD MINING FEE
        # Include the mining fee TXN in the block
        miningTXN = Transaction(simulator.mining_txn_id, current.pid, current.pid, 50, N.num_nodes)

        # Include it in the TXN list
        self.block.transactions.append(miningTXN.id)
        simulator.mining_txn_id-=1

        # To update the balances in the block
        current.update_balances(simulator, self.block)

        # Validate the block
        # If block is invalid, then destroy MineBlock Event - no need to validate on the receiving end - since this is only a simulator
        if not current.validate_block(simulator, self.block):
            print("BLOCK CREATION ERROR: BLOCK CONTAINS INVALID TXN")
            print("SEE INVALID BALANCES:", self.block.balances)
            return         
        
        print("MINING SUCCESSFUL: NEW BLOCK GENERATED")
        self.block.print_block()
        simulator.global_Blocks[self.block.block_id] = self.block

        # Add the block to my chain
        if not current.add_block(simulator, self.block):
            print("BLOCK ERROR on",current.pid,": ERROR IN ADDING BLOCK DUE TO VALIDATION")
            return False

        # Forwarding the block to its peers
        for neighbor in N.G.neighbors(self.node_id):

            # Exclude the crator of the block
            if neighbor != self.block.creator_id:

                t = N.get_latency(self.node_id, neighbor, self.block.get_size()) # To calculate the latency of the block based on the number of transactions in the block
                self.block.received[neighbor] = 1 # That the node has seen the block
                simulator.events.put(ForwardBlock(
                    self.block,
                    neighbor,
                    self.node_id,
                    self.run_time,
                    self.run_time + t
                ))

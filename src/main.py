import argparse
import os
import random
import shutil

from event import *
from simulate import Simulator

# Take command line arguments
cli = argparse.ArgumentParser() # Command line interface
cli.add_argument("-n","--nodes", type=int, default=25, help="Number of nodes") # Number of nodes
cli.add_argument("-z","--zeta", type=int, default=50, help="Percentage of nodes the adversary is connected to") # Percentage of nodes the adversary is connected to
cli.add_argument("-z0","--low_cpu", type=float, default=50, help="Percentage of slow nodes") # Percentage of slow nodes
cli.add_argument("-z1","--low_speed", type=float, default=50, help="Percentage of low CPU nodes") # Percentage of low CPU nodes
cli.add_argument("-T","--Ttx", type=float, default=10, help="Mean transaction interarrival time") # Mean transaction interarrival time
cli.add_argument("-I","--interarrival_block", type=float, default=15, help="Mean block interarrival time") # Mean block interarrival time
cli.add_argument("-t","--time", type=int, default=1000, help="The amount of time to run the simulation for") # The number of steps to run the simulation for
cli.add_argument("--type",type = int , default = 0, help = "Type of simulation to run. 0 for normal run, 1 for selfish mining and 2 for stubborn mining") # Type of simulation to run
cli.add_argument("-v","--visualize", action='store_true', help="Visualize the blockchain tree") # Visualize the blockchain tree
cli.add_argument("-d","--dump", action='store_true', help="Dump the blockchain tree") # Dump the blockchain tree
cli.add_argument("--normal", action='store_true', help="Run the simulation with normal nodes") # Run the simulation with normal nodes
cli.add_argument("-s","--save_progress", action='store_true', help="Show the progression with time")
cli.add_argument("-p","--print", action='store_true', help="Prints the output to the stdout")
cli.add_argument("-a","--adversary_hashing", type=int, default=-1, help="The hashing of the adversary") # The hashing of the adversary

args = cli.parse_args() # Parse the arguments

simulation_type = args.type

def main():
    simulator = Simulator(args.nodes,args.zeta,args.low_cpu,args.low_speed, args.Ttx, args.interarrival_block, args.time, simulation_type ,args.print, args.adversary_hashing)
    simulator.run()
######################################################################################################################################################################
    # To release the adversary's blocks after the simulation is over
    adv_node = simulator.N.nodes[0]
    for i in range(0,len(adv_node.private_blockchain)):
        block = adv_node.private_blockchain.pop(0)
        if args.print:
            print(f"Releasing adversary's block after end of simulation: {block.block_id}")
        received_list = [False]*simulator.N.num_nodes 
        received_list[0] = True
        forward_block(simulator,block,adv_node,received_list)
    simulator.env.run(until=args.time+100)
######################################################################################################################################################################
    folders = os.listdir()
    if args.visualize:
        print("Visualizing the blockchain tree...")
        simulator.print_blockchains(4,args.normal)
        simulator.visualize()
######################################################################################################################################################################    
    if 'blockchain_tree' in folders:
        shutil.rmtree('blockchain_tree')
    if 'networkx_graph' in folders:
        shutil.rmtree('networkx_graph')
    if 'ete3_graph' in folders:
        shutil.rmtree('ete3_graph')
        
    os.mkdir('blockchain_tree')
    os.mkdir('networkx_graph')
    os.mkdir('ete3_graph')

    if args.dump:
        print(f"Converting blockchain tree graphs to png and saving to networkx_graph. This step may take a while...")
        for node in simulator.N.nodes:
            node.dump_blockchain_tree()
            node.dump_networkx_graph(args.normal)
            node.dump_ete3_graph(args.normal)
######################################################################################################################################################################
    if args.save_progress:
        print("Dumping the progressions. This step may take a while...")
        if 'progress_0' in folders:
            shutil.rmtree('progress_0')
        if 'progress_1' in folders:
            shutil.rmtree('progress_1')
        os.mkdir('progress_0')
        os.mkdir('progress_1')
        for node in simulator.N.nodes[:2]:
            node.dump_progress()
###################################################################################################################################################################### 
    # For analysis
    total_blocks = 0
    total_adversary_blocks = 0
    blocks_in_longest_chain = 0
    adversary_blocks_in_longest_chain = 0

    node = simulator.N.nodes[1]
    longest_chain = node.find_longest_chain()
    for block_id, block in node.blockchain.items():
        total_blocks += 1
        if block.creator_id == 0:
            total_adversary_blocks += 1
        if block_id in longest_chain:
            blocks_in_longest_chain += 1
            if block.creator_id == 0:
                adversary_blocks_in_longest_chain += 1


    print(f"Total blocks (released or not): {total_blocks }")
    print(f"Total adversary blocks (released or not): {total_adversary_blocks}")
    print(f"Total blocks in longest chain: {blocks_in_longest_chain}")
    print(f"Adversary blocks in longest chain: {adversary_blocks_in_longest_chain}")

    print(f"Percentage of adversary blocks overall: {total_adversary_blocks/total_blocks}")

    print(f"Percentage of adversary blocks in longest chain: {adversary_blocks_in_longest_chain/blocks_in_longest_chain}")

    print("---------------------------------------------------------------------------------------------------------------")
    try:
        print(f"MPU_node_adv: {adversary_blocks_in_longest_chain/total_adversary_blocks}")
        print("---------------------------------------------------------------------------------------------------------------")
    except ZeroDivisionError:
        print("MPU_node_adv: 0")
        print("---------------------------------------------------------------------------------------------------------------")
    print(f"MPU_node_overall: {blocks_in_longest_chain/total_blocks}")
    print("---------------------------------------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
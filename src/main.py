import argparse
import os
import random
import shutil

from simulate import Simulator

# Take command line arguments
cli = argparse.ArgumentParser() # Command line interface
cli.add_argument("-n","--nodes", type=int, default=25, help="Number of nodes") # Number of nodes
cli.add_argument("-z","--zeta", type=int, default=50, help="Percentage of nodes the adversary is connected to") # Percentage of nodes the adversary is connected to
cli.add_argument("-z0","--low_cpu", type=float, default=0, help="Percentage of slow nodes") # Percentage of slow nodes
cli.add_argument("-z1","--low_speed", type=float, default=0, help="Percentage of low CPU nodes") # Percentage of low CPU nodes
cli.add_argument("--Ttx", type=float, default=10, help="Mean transaction interarrival time") # Mean transaction interarrival time
cli.add_argument("--I", type=float, default=4, help="Mean block interarrival time") # Mean block interarrival time
cli.add_argument("-t","--time", type=int, default=1000, help="The amount of time to run the simulation for") # The number of steps to run the simulation for
cli.add_argument("--type",type = int , default = 0, help = "Type of simulation to run. 0 for normal run, 1 for selfish mining and 2 for stubborn mining") # Type of simulation to run
cli.add_argument("-v","--visualize", action='store_true', help="Visualize the blockchain tree") # Visualize the blockchain tree
cli.add_argument("-d","--dump", action='store_true', help="Dump the blockchain tree") # Dump the blockchain tree
cli.add_argument("--normal", action='store_true', help="Run the simulation with normal nodes") # Run the simulation with normal nodes
cli.add_argument("-s","--show_progress", action='store_true', help="Show the progression with time")
cli.add_argument("-p","--print", action='store_true', help="Prints the output to the stdout")
cli.add_argument("-ah","--adversary_hashing", type=int, default=-1, help="The hashing of the adversary") # The hashing of the adversary

args = cli.parse_args() # Parse the arguments

simulation_type = args.type

if __name__ == "__main__":
    simulator = Simulator(args.nodes,args.zeta,args.low_cpu,args.low_speed, args.Ttx, args.I, args.time, simulation_type ,args.print, args.adversary_hashing)
    simulator.run()
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
        os.mkdir('blockchain_tree')
        os.mkdir('networkx_graph')
    if args.dump:
        print(f"Converting blockchain tree graphs to png and saving to networkx_graph. This step may take a while...")
        for node in simulator.N.nodes:
            node.dump_blockchain_tree()
            node.dump_networkx_graph(args.normal)
    if args.show_progress:
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

node = random.choice(simulator.N.nodes[1:])
longest_chain = node.find_longest_chain()
for block_id, block in node.blockchain.items():
    total_blocks += 1
    if block.creator_id == 0:
        total_adversary_blocks += 1
    if block_id in longest_chain:
        blocks_in_longest_chain += 1
        if block.creator_id == 0:
            adversary_blocks_in_longest_chain += 1

print(f"Total blocks: {total_blocks}")
print(f"Total adversary blocks: {total_adversary_blocks}")
print(f"Total blocks in longest chain: {blocks_in_longest_chain}")
print(f"Adversary blocks in longest chain: {adversary_blocks_in_longest_chain}")

print(f"Percentage of adversary blocks overall: {total_adversary_blocks/total_blocks}")

print(f"Percentage of adversary blocks in longest chain: {adversary_blocks_in_longest_chain/blocks_in_longest_chain}")

print("---------------------------------------------------------------------------------------------------------------")
print(f"MPU_node_adv: {adversary_blocks_in_longest_chain/total_adversary_blocks}")
print("---------------------------------------------------------------------------------------------------------------")
print(f"MPU_node_overall: {blocks_in_longest_chain/total_blocks}")
print("---------------------------------------------------------------------------------------------------------------")
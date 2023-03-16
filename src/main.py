import argparse
import os
import shutil

from simulate import Simulator

# Take command line arguments
cli = argparse.ArgumentParser() # Command line interface
cli.add_argument("--n", type=int, default=20, help="Number of nodes") # Number of nodes
cli.add_argument("--zeta", type=int, default=50, help="Percentage of nodes the adversary is connected to") # Percentage of nodes the adversary is connected to
cli.add_argument("--z0", type=float, default=0, help="Percentage of slow nodes") # Percentage of slow nodes
cli.add_argument("--z1", type=float, default=0, help="Percentage of low CPU nodes") # Percentage of low CPU nodes
cli.add_argument("--Ttx", type=float, default=10, help="Mean transaction interarrival time") # Mean transaction interarrival time
cli.add_argument("--I", type=float, default=4, help="Mean block interarrival time") # Mean block interarrival time
cli.add_argument("--time", type=int, default=1000, help="The amount of time to run the simulation for") # The number of steps to run the simulation for
cli.add_argument("-t","--type",type = int , default = 0, help = "Type of simulation to run. 0 for normal run, 1 for selfish mining and 2 for stubborn mining") # Type of simulation to run
cli.add_argument("-v","--visualize", action='store_true', help="Visualize the blockchain tree") # Visualize the blockchain tree
cli.add_argument("-d","--dump", action='store_true', help="Dump the blockchain tree") # Dump the blockchain tree
cli.add_argument("-n","--normal", action='store_true', help="Run the simulation with normal nodes") # Run the simulation with normal nodes

args = cli.parse_args() # Parse the arguments

simulation_type = args.type

if __name__ == "__main__":
    simulator = Simulator(args.n,args.zeta,args.z0,args.z1, args.Ttx, args.I, args.time, simulation_type)
    simulator.run()
if args.visualize:
    print("Visualizing the blockchain tree...")
    simulator.print_blockchains(4,args.normal)
    simulator.visualize()
######################################################################################################################################################################    
    folders = os.listdir()
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
###################################################################################################################################################################### 
node = simulator.N.nodes[0]
print(len(node.private_blockchain))
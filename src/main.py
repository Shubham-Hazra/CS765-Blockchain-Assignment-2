import argparse
import os
import shutil

from simulate import Simulator

# Take command line arguments
cli = argparse.ArgumentParser() # Command line interface
cli.add_argument("--n", type=int, default=50, help="Number of nodes") # Number of nodes
cli.add_argument("--z0", type=float, default=10, help="Percentage of slow nodes") # Percentage of slow nodes
cli.add_argument("--z1", type=float, default=40, help="Percentage of low CPU nodes") # Percentage of low CPU nodes
cli.add_argument("--Ttx", type=float, default=10, help="Mean transaction interarrival time") # Mean transaction interarrival time
cli.add_argument("--I", type=float, default=60, help="Mean block interarrival time") # Mean block interarrival time
cli.add_argument("--steps", type=int, default=10000, help="The number of steps to run the simulation for") # The number of steps to run the simulation for

args = cli.parse_args() # Parse the arguments

if __name__ == "__main__":
    simulator = Simulator(args.n, args.z0, args.z1, args.Ttx, args.I, args.steps)
    folders = os.listdir()
    if 'blockchain_tree' in folders:
        shutil.rmtree('blockchain_tree')
    if 'networkx_graph' in folders:
        shutil.rmtree('networkx_graph')
    os.mkdir('blockchain_tree')
    os.mkdir('networkx_graph')
    print(f"Converting blockchain tree graphs to png and saving to networkx_graph. This step may take a while...")
    for node in simulator.N.nodes:
        node.dump_blockchain_tree()
        node.dump_networkx_graph()
        

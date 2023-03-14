import argparse
import os
import shutil

from simulate import Simulator

# Take command line arguments
cli = argparse.ArgumentParser() # Command line interface
cli.add_argument("--n", type=int, default=20, help="Number of nodes") # Number of nodes
cli.add_argument("--zeta", type=int, default=10, help="Percentage of nodes the adversary is connected to") # Percentage of nodes the adversary is connected to
cli.add_argument("--z1", type=float, default=40, help="Percentage of low CPU nodes") # Percentage of low CPU nodes
cli.add_argument("--Ttx", type=float, default=100, help="Mean transaction interarrival time") # Mean transaction interarrival time
cli.add_argument("--I", type=float, default=0.6, help="Mean block interarrival time") # Mean block interarrival time
cli.add_argument("--time", type=int, default=1000, help="The amount of time to run the simulation for") # The number of steps to run the simulation for
cli.add_argument("--type",type = int , default = 1, help = "Type of simulation to run. 0 for normal run, 1 for selfish mining and 2 for stubborn mining") # Type of simulation to run
args = cli.parse_args() # Parse the arguments

simulation_type = args.type

if __name__ == "__main__":
    simulator = Simulator(args.n,args.zeta,args.z1, args.Ttx, args.I, args.time, simulation_type)
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
        

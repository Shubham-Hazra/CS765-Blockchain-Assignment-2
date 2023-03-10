import random

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from node import Node


class Network:
    def __init__(self, num_nodes,z0,z1,I):
        self.num_nodes = num_nodes; # Number of nodes in theconnected graph
        self.G = nx.Graph() # Stores the graph of the network
        self.adj = {} # Stores the dictionary of lists for storing the graph of the network
        self.create_graph() # create the P2P Network
        self.attrb = {} # Dictionary which contain attributes of each node (CPU and Speed)
        for i in range(self.num_nodes): # Initialize the dictionary
            self.attrb[i] = {}
        self.calc_speed(z0) # Sets z0 percent of nodes to low speed ("slow")
        self.calc_cpu(z1) # Sets z1 percent of nodes as low CPU
        self.set_attrb() # Sets the attributes of the nodes
        #-----------------------------------------------------------------------
        self.set_hashing_power(z1,I) # Sets the hashing power of the network
        self.set_static_latency() # Sets the latency of the network
        #-----------------------------------------------------------------------
        self.nodes = [Node(i, self.attrb[i],num_nodes) for i in range(self.num_nodes)] # Array of Node objects which have operations defined in them 

    # VERIFIED
    def create_graph(self):

        # Repeat while the graph is connected
        while True:
            self.G.add_nodes_from([i for i in range(self.num_nodes)])

            sequence = [random.randint(4,8) for i in range(self.num_nodes)] # Each node has 4 to 8 peers
            # Randomly generate a valid degree sequence
            while not nx.is_graphical(sequence, "hh"): # Check if the given degree sequence is valid 
                sequence = [random.randint(4,8) for i in range(self.num_nodes)]

            # Sort the degree sequence
            sequence.sort()
            curr_deg = [0 for i in range(self.num_nodes)] # Maintains the current degree of all the nodes

            # Connects the nodes of the graph
            for i in range(self.num_nodes-1, -1, -1):
                for j in range(i-1, -1, -1):
                    if curr_deg[i] == sequence[i]:
                        break
                    elif curr_deg[j] < sequence[j]:
                        self.G.add_edge(i,j)
                        curr_deg[i]+=1
                        curr_deg[j]+=1
            
            # Shuffle some nodes to introduce randomness
            nx.double_edge_swap(self.G, nswap=self.num_nodes/4, max_tries=1000, seed=None) # The number of swaps is a hyper parameter

            if nx.is_connected(self.G) and min([val for (node, val) in self.G.degree]) >= 4:
                break
            else:
                self.G.clear()

        # Converts Graph to dictionary of lists
        self.adj = nx.to_dict_of_lists(self.G, nodelist=None)
        print(self.adj)

        # Print the degree sequence
        print(sequence)

    # VERIFIED
    def show_graph(self):
        # Print the graph
        nx.draw(self.G, with_labels=True)
        plt.show()

    # VERIFIED
    def calc_cpu(self, z): # Sets z percent of nodes as low CPU 
        z = int(z*self.num_nodes/100.0)
        low_cpu = random.sample(list(range(self.num_nodes)), z) # Maintains a list of nodes whose CPU is set to low
        
        for i in range(self.num_nodes):
            if i in low_cpu:
                self.attrb[i]['cpu'] = 'low'
            else:
                self.attrb[i]['cpu'] = 'high'

    # VERIFIED
    def calc_speed(self, z): # Sets z percent of nodes to low speed ("slow")
        z = int(z*self.num_nodes/100.0)
        low_speed = random.sample(list(range(self.num_nodes)), z) # Maintains a list of nodes whose CPU is set to low
        
        for i in range(self.num_nodes):
            if i in low_speed:
                self.attrb[i]['speed'] = 'low'
            else:
                self.attrb[i]['speed'] = "high"

    # VERIFIED
    def set_attrb(self): # Sets the cpu and speed of the node calculated before
        nx.set_node_attributes(self.G, self.attrb)        

    # VERIFIED
    def set_static_latency(self):
        for edge in self.G.edges:
            node1 = edge[0]
            node2 = edge[1]
            # Minimum latency between two nodes is 10ms and maximum is 500ms due to the speed of light
            self.G[node1][node2]['p'] = np.random.uniform(10, 500)/1000

            if self.attrb[node1]['speed'] == 'low' or self.attrb[node2]['speed'] == 'low':
                self.G[node1][node2]['c'] = 5 # Link speed is 5Mbps if either of the nodes has low speed
            else:
                self.G[node1][node2]['c'] = 100 # Link speed is 100Mbps if both of the nodes have high speed

    # VERIFIED
    def get_latency(self, node1, node2, packet_size):  # returns the latency of the network # NOTE: Packet size in MB
        return self.G[node1][node2]['p'] + packet_size/self.G[node1][node2]['c'] + random.expovariate((self.G[node1][node2]['c']*1000)/96) # Queueing delay at node 1

    # VERIFIED
    def set_hashing_power(self,z, I):
        for i in range(self.num_nodes): # Sets the I value for all the nodes of the network
            self.attrb[i]['I'] = I

        k = int(z*self.num_nodes/100.0)
        hashing_power = 1/(k + 10*(self.num_nodes - k))
        for i in range(self.num_nodes):
            if self.attrb[i]['cpu'] == 'low':
                self.attrb[i]['hashing_power'] = hashing_power
            else:
                self.attrb[i]['hashing_power'] = hashing_power*10

# # Testing the class
# N = Network(15,10,10,600)
# print("CPU power of first node" , N.G.nodes[0]['cpu'])
# N.show_graph()
# for edge in N.G.edges:
#     print("Latency between the nodes of the first edge (in seconds): ", N.get_latency(edge[0],edge[1],17))
#     break





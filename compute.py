#!/usr/bin/python

from triplegraph import TripleGraph

import argparse

parser = argparse.ArgumentParser(description='Running Graph Mining Algorithms')
parser.add_argument('--endpoint')

args = parser.parse_args()
print(args)


if __name__ == '__main__':
    
    gdb = TripleGraph()
    print ""
    if args.endpoint is not None:
        gdb.init_graph(endpoint_url = args.endpoint)
    else:
        gdb.init_graph()
            
    gdb.eccentricity("12", maxIteration = 30, toFile = True)
    gdb.personalized_pagerank(personalization = {1:0.5, 3:0.2, 5:0.1}, toFile = True, maxIteration = 50)
    gdb.pagerank(toFile = True, maxIteration = 50)
    gdb.single_source_shortest_path(startNodeID="12", maxIteration = 30, toFile = True)
    gdb.multi_source_shortest_path(startNodeID="12", endNodeID="6", toFile = True)
    gdb.connected_component(toFile = True)
    gdb.peer_pressure_clustering(toFile = True, maxIteration = 10)

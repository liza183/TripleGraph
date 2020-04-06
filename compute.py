#!/usr/bin/python

from graphka import GraphDB

if __name__ == '__main__':
    
    gdb = GraphDB()
    print ""
    gdb.init_graph()
        
    gdb.eccentricity("12", maxIteration = 30, toFile = True)
    gdb.personalized_pagerank(personalization = {1:0.5, 3:0.2, 5:0.1}, toFile = True, maxIteration = 50)
    gdb.pagerank(toFile = True, maxIteration = 50)
    gdb.single_source_shortest_path(startNodeID="12", maxIteration = 30, toFile = True)
    gdb.multi_source_shortest_path(startNodeID="12", endNodeID="6", toFile = True)
    gdb.connected_component(toFile = True)
    gdb.peer_pressure_clustering(toFile = True, maxIteration = 10)

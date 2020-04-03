'''
Created on Apr 8, 2015

@author: matt lee

'''

from gdb import GraphDatabase

if __name__ == '__main__':
    
    gdb = GraphDatabase()
    print ""
    gdb.init_graph()
    
    #gdb.clear_graph()
    #nodeFilePath="../data/hetrec/nodes.json"
    #edgeFilePath="../data/hetrec/edges.json"
    #gdb.json_loader(nodeFilePath, edgeFilePath)

    #gdb.clear_graph()
    #edgeListFilePath="../data/example/edgelist_1.txt"
    #gdb.edgelist_loader(edgeListFilePath, bidirectional = True)
    
    gdb.clear_graph()
    edgeListFilePath="../data/astro/ca-AstroPh.txt"
    gdb.edgelist_loader(edgeListFilePath, bidirectional = True)

    #gdb.clear_graph()
    #edgeListFilePath="../data/dblp/com-dblp.ungraph.txt"
    #gdb.edgelist_loader(edgeListFilePath, bidirectional = True)

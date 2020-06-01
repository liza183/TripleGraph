#!/usr/bin/python
import sys

import argparse

parser = argparse.ArgumentParser(description='Data Bulk import Tool for GraphKa')
parser.add_argument('--edgelist')
parser.add_argument('--json')
parser.add_argument('--endpoint')
parser.add_argument('--bidirectional', dest = 'bidirectional', action='store_true')
parser.set_defaults(bidirectional=False)

args = parser.parse_args()

from triplegraph import TripleGraph

if __name__ == '__main__':
    
    gdb = TripleGraph()
    print ""
    if args.endpoint is not None:
        gdb.init_graph(endpoint_url = args.endpoint)
    else:
        gdb.init_graph()
    
    if args.edgelist is not None:

        gdb.clear_graph()
        gdb.edgelist_loader(args.edgelist, bidirectional = args.bidirectional)

    elif args.json is not None:

        gdb.clear_graph()
        nodeFilePath=args.json+"/nodes.json"
        edgeFilePath=args.json+"/edges.json"
        gdb.json_loader(nodeFilePath, edgeFilePath)
        gdb.edgelist_loader(args.edgelist, bidirectional = args.bidirectional)
    
    print ""
    print " * Done"
    print ""

# GraphEureka

* GraphEureka is a graph processing toolkit for creating, manipulating, and analyzing large scale graphs, which uses a JENA triple store as the system's internal data processing engine. 

# Main functionalities:

* Compatible with JENA Fuseki
    * Although primarily developed for Cray's Urika hosted at the Department of Energy's Oak Ridge National Laboratory, this open source version works on Apache Jena triplestore. 

* Compatible with Cray Urika-GD (Graph processing appliance)
    * not supported by open-source version

* Data import tool for JSON, edgelist formatted graph data
* Both homogeneous & property graph are supported
* Node/edge retrieval and manipulation
* Path finding
* Pregel-like abstracted graph processing operations
    * Aggregate Neighbor Labels
    * Label Propagate
* Pre-implemented Graph algorithms
    * PageRank/Personalized PageRank
    * Single Source Shortest Path/Multi Source Shortest Path
    * Connected Component
    * Eccentricity
    * Peer Pressure Clustering

# Releases

* The current version is experimental version.

# Requirements

* JENA Fuseki1 or compatable triplestore servers

# Example

* Run GraphEureka (please see the source code for more details)

```
#!

Matts-MacBook-Pro:src liza183$ python
Python 2.7.6 (default, Sep  9 2014, 15:04:36) 
[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.39)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import gdb
>>> g = gdb.GraphDatabase()
>>> g.init_graph()
 - msg: Initializing the graph ...
>>> g.clear_graph()
 - msg: Graph cleared ...
>>> g.edgelist_loader("/Users/liza183/Playground/developments/gdb/src/data/example/edgelist.txt", bidirectional = True)
 - msg: loading edges :0 line processed
 - msg: loading edges :13 line processed
 - msg: Generating nodes from edges ...
 - msg: Making the graph bidirectional ...
>>> print g.get_node_num()
15
>>> print g.get_node("1")
{'type': u'None', 'nodeID': '1'}
>>> print g.get_edge("1")
{'type': u'None', 'edgeID': '1'}
>>> print g.get_path("1","2",path_len=2)
[[('1', '11', '3'), ('3', '12', '2')]]
>>> g.connected_component(toFile = True)

 - msg: Labels cleared ...
 - msg: Performing Connected Component ...
iteration no : 0
Elapsed Time: 0.0241920948029 seconds.
iteration no : 1
Elapsed Time: 0.0225391387939 seconds.
iteration no : 2
Elapsed Time: 0.0174908638 seconds.
iteration no : 3
Elapsed Time: 0.016725063324 seconds.
iteration no : 4
Elapsed Time: 0.0313160419464 seconds.
 - msg: 15 results written in file: result/cc_1427809424.88.txt
>>> g.pagerank(toFile = True)

 - msg: Labels cleared ...
 - msg: Performing PageRank ...
iteration no : 0
Elapsed Time: 0.0250759124756 seconds.
iteration no : 1
Elapsed Time: 0.024551153183 seconds.
iteration no : 2
Elapsed Time: 0.0205080509186 seconds.
iteration no : 3
Elapsed Time: 0.0228900909424 seconds.
iteration no : 4
Elapsed Time: 0.0221910476685 seconds.
iteration no : 5
Elapsed Time: 0.0236821174622 seconds.
iteration no : 6
Elapsed Time: 0.0224869251251 seconds.
iteration no : 7
Elapsed Time: 0.0217940807343 seconds.
 - msg: 15 results written in file: result/pr_1427809439.74.txt
>>>
```

# Things that need to be done before public release

* Very simple performance analysis vs. network X
* pip installation or simpler installation process
* explanation about back-end
* backend setup more flexible (like port number etc.)
* remove the reason to init the graph
* remove cray code and use SPARQLWrapper instead
* The current version has a limitation of keeping only one graph in a triplestore. 
* 
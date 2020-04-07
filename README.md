# TripleGraph

* TripleGraph is a graph analysis and programming toolkit for creating, manipulating, and analyzing large scale property graphs, which uses a RDF tripletore as its backend.
* Although primarily developed for Cray's Urika-GD system hosted at the Department of Energy's Oak Ridge National Laboratory, this open source version works on Apache Jena Fuseki/TDB triplestore. 

# Main functionalities:

* Importing edgelist-formatter (homogeneous graph) or JSON-formatted graph (property graph) 
* Node/edge retrieval and manipulation
* Path finding between two given nodes
* Running graph mining algorithms
    * PageRank/Personalized PageRank
    * Single Source Shortest Path/Multi Source Shortest Path
    * Connected Component
    * Eccentricity
    * Peer Pressure Clustering
* Users can implement his/her own graph mining algorithms using Pregel-like abstracted graph processing operations
    * Aggregate Neighbor Labels
    * Label Propagate

# Releases

* The current version is experimental version (v0.1).

# Requirements

* JENA Fuseki1/2 or compatable triplestore servers
   * Download link: https://jena.apache.org/documentation/fuseki2/
* Python 2.7

* Please see requirements.txt to see required packages

# Getting started with TripleGraph

* Run Jena Fuseki
```
apache-jena-fuseki-3.14.0 $ java -Xms4G -Xmx12G -jar fuseki-server.jar --update --mem /ds
[2020-04-07 12:00:54] Server     INFO  Dataset: in-memory
[2020-04-07 12:00:54] Server     INFO  Apache Jena Fuseki 3.14.0
[2020-04-07 12:00:54] Config     INFO  FUSEKI_HOME=/Users/slz/git_projects/graph-eureka/apache-jena-fuseki-3.14.0/.
[2020-04-07 12:00:54] Config     INFO  FUSEKI_BASE=/Users/slz/git_projects/graph-eureka/apache-jena-fuseki-3.14.0/run
[2020-04-07 12:00:54] Config     INFO  Shiro file: file:///Users/slz/git_projects/graph-eureka/apache-jena-fuseki-3.14.0/run/shiro.ini
[2020-04-07 12:00:54] Config     INFO  Template file: templates/config-mem
[2020-04-07 12:00:55] Config     INFO  Register: /ds
[2020-04-07 12:00:55] Server     INFO  Started 2020/04/07 12:00:55 EDT on port 3030
```
Now the server is running (dataset is in-memory, volatile) on localhost port 3030.

* Data Import from a edgelist file

```
(base) slzmbpro:graph-eureka slz$ ./import.py --edgelist data/example/edgelist.txt 

 - msg: Initializing the graph ...
 - msg: Graph cleared ...
 - msg: loading edges :0 line processed
 - msg: loading edges :13 line processed
 - msg: Generating nodes from edges ...

 * Done

(base) slzmbpro:graph-eureka slz$
```

* Running graph mining algorithms (after the data is imported)

```
$ ./compute.py 

 - msg: Initializing the graph ...

 - msg: Computing eccentricity...

 - msg: Labels cleared ...
 - msg: Performing single source shortest path...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0677628517151 seconds.
 - msg: The result (eccentricity = 0) written in file: result/ec_1586275434.42.txt

 - msg: Labels cleared ...
 - msg: Performing Personalized PageRank ...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0296740531921 seconds.
 - msg: iteration no: 1
 - msg: Elapsed Time: 0.0222589969635 seconds.
 - msg: 15 results written in file: result/ppr_1586275434.53.txt

 - msg: Labels cleared ...
 - msg: Performing PageRank ...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0200660228729 seconds.
 - msg: 15 results written in file: result/pr_1586275434.58.txt

 - msg: Labels cleared ...
 - msg: Performing single source shortest path...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0231919288635 seconds.
 - msg: 15 results written in file: result/sspp_1586275434.64.txt

 - msg: Labels cleared ...
 - msg: Performing multi source shortest path...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0229070186615 seconds.
 - msg: The shortest distance between two nodes (12 and 6) = 9999 written in file: result/mssp_1586275434.69.txt

 - msg: Labels cleared ...
 - msg: Performing Connected Component ...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0217750072479 seconds.
 - msg: iteration no: 1
 - msg: Elapsed Time: 0.0204210281372 seconds.
 - msg: 15 results written in file: result/cc_1586275434.75.txt

 - msg: Labels cleared ...
 - msg: Performing Peer Pressure Clustering ...
 - msg: iteration no: 0
 - msg: Elapsed Time: 0.0365810394287 seconds.
 - msg: iteration no: 1
 - msg: Elapsed Time: 0.0282709598541 seconds.
 - msg: 15 results written in file: result/pp_1586275434.84.txt
```
# License

* Please contact Matt Sangkeun Lee for more information: lees4@ornl.gov

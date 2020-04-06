# This project is experimental
# Property Graph Programming Interface for Triplestores
# Programmed by Sangkeun Lee (leesangkeun@gmail.com)

from SPARQLWrapper import *
import logging
import ast
import re
import traceback
import time
import random

logging.basicConfig(level = logging.CRITICAL)

class GraphDB:    

    def query(self, query_str):
        self.connection.setQuery(query_str)
        self.connection.setReturnFormat(JSON)
        results = self.connection.query().convert()
        return results

    def update(self, query_str):
        self.connection.setMethod(POST)
        self.connection.setQuery(query_str)
        self.connection.setReturnFormat(JSON)
        results = self.connection.query()


    def is_number(self, s):
        
        if s.lower()=="infinity":
            return False

        try:
            float(s)
            return True
        except ValueError:
            return False

    def propagate_label(self, key, val= None, nextKey=None, forceToString = False, customPropagateClause="?value", includeItself = False):
        

        if nextKey == None:
            nextKey = key

        if includeItself == False:
            includeItselfClause = ""
        else:
            includeItselfClause = """

            union {{
                select (?s as ?neighbor) (?value as ?insert_value) 
                    {{
                        graph <gdb:label> {{?s <label:{0}> ?value}} 
                    }}
                }}

            """

            includeItselfClause = includeItselfClause.format(key)

        PROPAGATE_QUERY = """

        INSERT {{ GRAPH <gdb:label> {{ ?neighbor <label:{1}> ?insert_value }}}}
            WHERE
            {{     
                {{
                    select distinct ?neighbor (({2}) as ?insert_value)
                    {{
                    {{graph <gdb:label> {{?s <label:{0}> ?value}}}}
                    {{graph <gdb:topology> {{?s ?edge ?neighbor}}}}
                    {3}
                    }}
                }}

                union {{
                select (?s as ?neighbor) ({2} as ?insert_value) 
                    {{
                        graph <gdb:label> {{?s <label:visited> ?value}} 
                        {3}
                    }}
                }}

                {4}
                NOT EXISTS {{ GRAPH <gdb:label> {{ ?neighbor <label:{1}> ?insert_value. }} }}

            }}

        """

        if val == None:
            filterClause = ""
        else:
            val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))
            if self.is_number(val)==False or forceToString==True:
                val = "\""+str(val)+"\""

            filterClause = "FILTER (?value = "+val+")"

        queryToExecute = PROPAGATE_QUERY.format(key, nextKey, customPropagateClause, filterClause, includeItselfClause)
        self.update(queryToExecute)

    def copy_node_label(self, key, nextKey, val = None, move = False):

        if val == None:
            val = "?o"
        else:
            val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))
            if self.is_number(val)==False or forceToString==True:
                val = "\""+str(val)+"\""

        AGGREGATE_LABEL = """
                
            {MOVE_CLAUSE}
            insert {{graph <gdb:label> {{?s <label:{1}> {2}}}}}
            where {{graph <gdb:label> {{?s <label:{0}> {2}}}}}

            """
        if move == True:
            moveClause = "delete {{graph <gdb:label> {{?s <label:{0}> {1}}}}}"
            moveCluase = moveCluase.format(key, val)
        else:
            moveClause = ""

        queryToExecute = AGGREGATE_LABEL.format(key, nextKey, val, MOVE_CLAUSE = moveClause)
        #print queryToExecute
        self.update(queryToExecute)
                
    def aggregate_labels(self, key, customAggregateClause, nextKey = None):

        if nextKey == None:
            nextKey = key

        AGGREGATE_LABEL = """
            delete {{graph <gdb:label> {{?s <label:{0}> ?original}}}}
            insert {{graph<gdb:label> {{?s <label:{1}> ?reduced}}}} 
            where {{
                select * {{
                    {{graph <gdb:label> {{?s <label:{0}> ?original}}
                }}

                {{
                select ?s ({2} as ?reduced) {{graph <gdb:label> {{?s <label:{0}> ?label}}}} group by ?s}}
                }}
            }}
        """
        queryToExecute = AGGREGATE_LABEL.format(key, nextKey, customAggregateClause)
        self.update(queryToExecute)

    def aggregate_neighbor_labels_custom(self, key, customAggregateClause, includeItself = False, nextKey = None, noReturn = False, minDifference = 0):

        if nextKey == None:
            nextKey = key

        # over threshold
        if minDifference >0: 
            minDifferenceClause = """
                        {{ GRAPH <gdb:label>
                            {{ ?v <label:{0}> ?original . }}
                        }}

                        FILTER (ABS(?original - ?update)>={1}).

            """
            minDifferenceClause = minDifferenceClause.format(key, minDifference)

        # at least should exist
        elif minDifference==0: 

            minDifferenceClause = """
                        {{ GRAPH <gdb:label>
                            {{ ?v <label:{0}> ?original . }}
                        }}

                        FILTER (?original!=?update).

            """
            minDifferenceClause = minDifferenceClause.format(key)

        # at least should exist
        elif minDifference==-1: 

            minDifferenceClause = """
                        {{ GRAPH <gdb:label>
                            {{ ?v <label:{0}> ?original . }}
                        }}

                        FILTER (?original<?update).

            """
            minDifferenceClause = minDifferenceClause.format(key)

        elif minDifference==-2: 

            minDifferenceClause = """
                        {{ GRAPH <gdb:label>
                            {{ ?v <label:{0}> ?original . }}
                        }}

                        FILTER (?original>?update).

            """
            minDifferenceClause = minDifferenceClause.format(key)

        else:
            minDifferenceClause = ""

        if '?indegree' in customAggregateClause:
            getInDegreeInfoClause = """
                {{
                    graph <gdb:info> {{?neighbor <rel:hasInDegree> ?indegree}}
                }}
            """
            getInDegreeInfoClauseForItself = """
            {{
                graph <gdb:info> {{?v <rel:hasInDegree> ?indegree}}
            }}
            """
        else:
            getInDegreeInfoClause =""
            getInDegreeInfoClauseForItself =""

        if '?outdegree' in customAggregateClause:
            getOutDegreeInfoClause = """
                {{
                    graph <gdb:info> {{?neighbor <rel:hasOutDegree> ?outdegree}}
                }}
            """
            getOutDegreeInfoCaluseForItself = """
                {{
                    graph <gdb:info> {{?v <rel:hasOutDegree> ?outdegree}}
                }}
            """
        else:
            getOutDegreeInfoClause =""
            getOutDegreeInfoClauseForItself =""
            
        if 'min(' in customAggregateClause.lower() and 'max(' not in customAggregateClause.lower():
            minmaxOptimizeClause = """
                                {{ GRAPH <gdb:label>
                                    {{ ?v <label:{0}> ?minimum . }}
                                }}
                                
                                FILTER (STR(?minimum) > STR(?label))
            """
            minmaxOptimizeClause = minmaxOptimizeClause.format(key)

        elif 'max(' in customAggregateClause.lower() and 'min(' not in customAggregateClause.lower():
            minmaxOptimizeClause = """
                                {{ GRAPH <gdb:label>
                                    {{ ?v <label:{0}> ?maximum . }}
                                }}
                                
                                FILTER (STR(?maximum) < STR(?label))
            """
            minmaxOptimizeClause = minmaxOptimizeClause.format(key)

        else:
            minmaxOptimizeClause = ""    

        minmaxOptimizeClause = ""

        includeItselfClause = ""
        
        if includeItself == True:
            
            includeItselfClause = """
                                union
                                {{
                                    {{
                                    
                                    {{
                                        graph <gdb:label> {{?v <label:{0}> ?label}}
                                    }}
                                    
                                    }}
                                    {1}
                                    {2}
                                    
                                }}

            """
            includeItselfClause = includeItselfClause.format(key,getInDegreeInfoClauseForItself,getOutDegreeInfoClauseForItself)

        if noReturn == True:
            countReturnClause = ""
            deleteReturnCountClause = ""

        else:
            countReturnClause = "<tmp:updated> 1 ."
            deleteReturnCountClause ="""
                DELETE { GRAPH <gdb:label> { ?s <tmp:updated> ?o . }}
                WHERE { GRAPH <gdb:label> { ?s <tmp:updated> ?o . }};
            """

        AGG_NEIGHBOR_QUERY = """
                
                {7}
                DELETE {{ GRAPH <gdb:label> {{ ?v <label:{0}> ?original . }}}}
                INSERT {{ GRAPH <gdb:label> {{ ?v <label:{2}> ?update ; {6} }}}}
                    WHERE
                    {{    
                        {{
                            select ?v ({1} as ?update) {{
                            
                                {{
                                    {{
                                    
                                    {{
                                        graph <gdb:label> {{?neighbor <label:{0}> ?label}}
                                    }}
                                    {{
                                        graph <gdb:topology> {{?v ?edge ?neighbor}}
                                    }}
                                    
                                    }}
                                    {4}
                                    {5}
                                    {8}
                                }}

                                {3}

                            }} 
                            
                            group by ?v
                        }}
                        
                        {9}
                        NOT EXISTS {{ GRAPH <gdb:label> {{ ?v <label:{2}> ?update . }} }}
                    }}

        """

        queryToExecute = AGG_NEIGHBOR_QUERY.format(key, customAggregateClause, nextKey, includeItselfClause,getInDegreeInfoClause,getOutDegreeInfoClause, countReturnClause, deleteReturnCountClause, minmaxOptimizeClause, minDifferenceClause)
        #print queryToExecute
        self.update(queryToExecute)
        updatedNo = 0

        if noReturn == False:
            GET_UPDATED_NUMBER = """
            select (count(*) as ?cnt) {graph <gdb:label> {?v <tmp:updated> 1}}
            """
            results = self.query(GET_UPDATED_NUMBER)
            
            for result in results['results']['bindings']:
                updatedNo = int(result['cnt']['value'])

        return updatedNo

    def aggregate_neighbor_labels_voting(self, key, nextKey = None, noReturn = False, includeItself = False, minDifference = 0):

        # over threshold
        if minDifference >0: 
            minDifferenceClause = """
                        {{ GRAPH <gdb:label>
                            {{ ?v <label:{0}> ?original . }}
                        }}

                        FILTER (ABS(?original - ?update)>={1}).

            """
            minDifferenceClause = minDifferenceClause.format(key, minDifference)

        # at least should exist
        elif minDifference==0: 

            minDifferenceClause = """
                        {{ GRAPH <gdb:label>
                            {{ ?v <label:{0}> ?original . }}
                        }}

                        FILTER (?original!=?update).

            """
            minDifferenceClause = minDifferenceClause.format(key)

        else:
            minDifferenceClause = ""
    
        includeItselfClause = ""
        
        if includeItself == True:
            
            includeItselfClause = """
                                
                                union
                                
                                {{
                                    select (?s as ?node) ?adj_label
                                    {{
                                          graph <gdb:label> {{?s <label:{0}> ?adj_label}}
                                    }}
                                }}


            """
            includeItselfClause = includeItselfClause.format(key)
    
        if noReturn == True:
            countReturnClause = ""
            deleteReturnCountClause = ""

        else:
            countReturnClause = ";<tmp:updated> 1 ."
            deleteReturnCountClause ="""
                DELETE { GRAPH <gdb:label> { ?s <tmp:updated> ?o . }}
                WHERE { GRAPH <gdb:label> { ?s <tmp:updated> ?o . }};
            """

        if nextKey == None:
            nextKey = key

        AGG_NEIGHBOR_QUERY = """
                    
                    {DELETE_RETURN}

                    DELETE {{ GRAPH <gdb:tmp> {{ ?s ?p ?o . }}}}
                    WHERE {{ GRAPH <gdb:tmp> {{ ?s ?p ?o . }}}};

                    insert {{graph <gdb:tmp> {{?node ?adj_label_uri ?cnt}}}} 
                    where {{
                        select ?node ?adj_label_uri (count(*) as ?cnt) {{
                            select ?node (uri(?adj_label) as ?adj_label_uri) {{
                                
                                {{  
                                    select (?s as ?node) ?adj_label
                                    {{
                                          {{graph <gdb:topology> {{?s ?p ?o.}}}}
                                          {{graph <gdb:label> {{?o <label:is_in_cluster> ?adj_label}}}}
                                    }} 
                                }}
                                
                                {INCLUDE_ITSELF}
                            }}
                        }} group by ?node ?adj_label_uri 
                    }};

                    DELETE {{ GRAPH <gdb:label> {{ ?node <label:{0}> ?original . }}}}
                    INSERT {{ GRAPH <gdb:label> {{ ?node <label:{1}> ?update {COUNT_CLAUSE} }}}}
                        WHERE
                        {{    
                            {{
                                {{
                                    select ?node (min(?adj_label) as ?update) {{
                                    {{
                                        select ?node (max(?cnt) as ?maxClusCnt) {{                
                                            select ?node ?adj_label ?cnt 
                                            {{graph <gdb:tmp> {{?node ?adj_label ?cnt}}}}
                                        }} group by ?node
                                    }}
                                    {{
                                    select ?node ?adj_label ?cnt {{graph <gdb:tmp> {{?node ?adj_label ?cnt}}}}
                                    }}
                                    filter(?cnt=?maxClusCnt)
                                    }} group by ?node
                                }}
                            }}

                            {{ GRAPH <gdb:label>
                                {{ ?node <label:{0}> ?original . }}
                            }}
                            FILTER (?original != ?update)
                        }}

            """

        queryToExecute = AGG_NEIGHBOR_QUERY.format(key, nextKey, DELETE_RETURN = deleteReturnCountClause, COUNT_CLAUSE = countReturnClause, INCLUDE_ITSELF = includeItselfClause)
        #print queryToExecute
        
        self.update(queryToExecute)
        updatedNo = 0

        if noReturn == False:
            GET_UPDATED_NUMBER = """
            select (count(*) as ?cnt) {graph <gdb:label> {?v <tmp:updated> 1}}
            """
            results = self.query(GET_UPDATED_NUMBER)
            
            for result in results['results']['bindings']:
                updatedNo = int(result['cnt']['value'])

        #print updatedNo
        return updatedNo

    def aggregate_neighbor_labels(self, key, aggregateClause , includeItself = False, nextKey = None, noReturn = False, minDifference = 0):
        
        updateNo = 0

        if aggregateClause == "voting":
            updateNo = self.aggregate_neighbor_labels_voting(key, nextKey, noReturn, includeItself, minDifference)
        else:
            updateNo = self.aggregate_neighbor_labels_custom(key, aggregateClause, includeItself, nextKey, noReturn, minDifference)
        
        return updateNo

    def make_graph_bidirectional(self):


        print " - msg: Making the graph bidirectional ..."

        queryToExecute = """
                insert {graph <gdb:topology> {?o ?p ?s} }where {
                select ?s ?p ?o {graph <gdb:topology> {?s ?p ?o}}
                }
            """

        self.update(queryToExecute)

    def gen_nodes_from_edges(self):

        print " - msg: Generating nodes from edges ..."

        queryToExecute = """

                insert {graph <gdb:vlist> {?s <rel:hasNodeType> <nodeType:None>} }where {
                select distinct ?s {
                {
                select distinct ?s {graph <gdb:topology> {?s ?p ?o}} 
                }
                union
                {
                select distinct ?s {graph <gdb:topology> {?o ?p ?s}} 
                }
                }}

            """

        self.update(queryToExecute)

    def edgelist_loader(self, edgeListFilePath, delim = '\t', bidirectional = False):

        f = open(edgeListFilePath,'r')
        
        lineNo = 0
        batchQuery = ""

        while True:

            line = f.readline()
            if not line : break
            
            if line.strip()[0]=='#':
                pass
            else:
               
                parsedLine = line.strip().split(delim)
                if(lineNo%5000==0):
                    if batchQuery!="": 
                        try:
                            self.update(batchQuery)
                        except:
                            fw = open('error.log','w')
                            fw.write(batchQuery)
                            fw.close()
                            traceback.print_exc()
                            print "ERROR! please see error.log for more detail"
                            break

                    print " - msg: loading edges :"+ str(lineNo)+" line processed"
                    batchQuery = ""
                
                lineNo+=1

                fromNodeID =  parsedLine[0]
                toNodeID =  parsedLine[1]
                
                batchQuery+= self.add_edge(fromNodeID, toNodeID, edgeType = None, fromNodeType=None, toNodeType=None, properties=None, execute = False, create_node=False, bidirectional = False, noReturn = True, gdbinfo_update = False)['query']
            
        if batchQuery!="":    

            try:
                self.update(batchQuery)
            except:
                fw = open('error.log','w')
                fw.write(batchQuery)
                fw.close()
                traceback.print_exc()
                print "ERROR! please see error.log for more detail"
        print " - msg: loading edges :"+ str(lineNo)+" line processed"  
        
        self.gen_nodes_from_edges()

        if bidirectional=="True" or bidirectional is True:
            self.make_graph_bidirectional()

        f.close()

        self.update_indegree_info_all()
        self.update_outdegree_info_all()

    def json_node_loader(self, nodeFilePath):
        f = open(nodeFilePath,'r')
        
        lineNo = 0
        batchQuery = ""

        while True:

            line = f.readline()
            if not line: break

            if(lineNo%500==0):

                if batchQuery!="":
                    
                    try:
                        self.update(batchQuery)
                    except:
                        fw = open('error.log','w')
                        fw.write(batchQuery)
                        fw.close()
                        traceback.print_exc()
                        print "ERROR! please see error.log for more detail"
                        break

                print " - msg: loading nodes :"+ str(lineNo)+" line processed"
                batchQuery = ""

            lineNo+=1

            properties = ast.literal_eval(line)
            nodeType =  properties.pop("_type", None)
            nodeID =  properties.pop("_id", None)
            
            batchQuery+= self.add_node(nodeID, nodeType, properties, execute=False, gdbinfo_update = False)
            
        if batchQuery!="":    
            try:
                self.update(batchQuery)
            except:
                fw = open('error.log','w')
                fw.write(batchQuery)
                fw.close()
                traceback.print_exc()
                print "ERROR! please see error.log for more detail"
        print " - msg: loading nodes :"+ str(lineNo)+" line processed"  

        f.close()

    def json_edge_loader(self, edgeFilePath):
        
        f = open(edgeFilePath,'r')
        
        lineNo = 0
        batchQuery = ""

        while True:

            line = f.readline()
            if(lineNo%500==0):

                if batchQuery!="":
                    
                    try:
                        self.update(batchQuery)
                    except:
                        fw = open('error.log','w')
                        fw.write(batchQuery)
                        fw.close()
                        traceback.print_exc()
                        print "ERROR! please see error.log for more detail"
                        break

                print "loading edges :"+ str(lineNo)+" line processed"
                batchQuery = ""

            if not line: break
            lineNo+=1

            properties = ast.literal_eval(line)
            fromNodeID =  properties.pop("_from_id", None)
            toNodeID =  properties.pop("_to_id", None)
            edgeType = properties.pop("_type", None)

            batchQuery+= self.add_edge(fromNodeID, toNodeID, edgeType=edgeType, fromNodeType=None, toNodeType=None, properties=properties, execute = False, create_node=False, noReturn = True, gdbinfo_update = False)['query']
            
        f.close()
        
        if batchQuery!="":
                    
            try:
                self.update(batchQuery)
            except:
                fw = open('error.log','w')
                fw.write(batchQuery)
                fw.close()
                traceback.print_exc()
                print "ERROR! please see error.log for more detail"

        print "loading edges :"+ str(lineNo)+" line processed"   

    def json_loader(self, nodeFilePath, edgeFilePath):
        
        self.json_node_loader(nodeFilePath)
        self.json_edge_loader(edgeFilePath)   
        self.update_indegree_info_all()
        self.update_outdegree_info_all()

    def clear_labels(self, key, val = None):
        if val == None:
            val = "?o"

        clear_graph_DB = """
        DELETE {{GRAPH <gdb:label> {{?s <label:{0}> {1}}}}} where {{GRAPH <gdb:label> {{?s <label:{0}> {1} }}}};
        """

        queryToExecute = clear_graph_DB.format(key, val)
        self.update(queryToExecute)

        print " - msg: Labels cleared ..."

    def clear_labels_all(self):
        clear_graph_DB = """
        DROP GRAPH <gdb:label> ;
        """

        #print ADD_A_NODE_QUERY.format(nodeID)
        self.update(clear_graph_DB)

        print " - msg: Labels cleared ..."

    def clear_graph(self):

        clear_graph_DB = """
        DROP GRAPH <gdb:vlist> ;
        DROP GRAPH <gdb:elist> ;
        DROP GRAPH <gdb:label> ;
        DROP GRAPH <gdb:topology> ;
        DROP GRAPH <gdb:info> ;
        DROP GRAPH <gdb:tmp> ;
        INSERT DATA {GRAPH <gdb:info> {<gdb:edgeIDCounter> <rel:equals> 0}};
        """

        #print ADD_A_NODE_QUERY.format(nodeID)
        self.update(clear_graph_DB)

        print " - msg: Graph cleared ..."

    def init_graph(self):

        print " - msg: Initializing the graph ..."
        self.connection = SPARQLWrapper("http://localhost:3030/ds")
        self.name = "gdb"

    def add_node(self, nodeID, nodeType=None, properties = None, execute = True, gdbinfo_update = True):
        
        ADD_A_NODE_QUERY = """
        
        DELETE {{
                GRAPH <gdb:vlist> {{<nodeID:{0}> ?p ?o}} 
            }}
        WHERE {{
                GRAPH <gdb:vlist> {{<nodeID:{0}> ?p ?o}}
            }}
        ;

        INSERT {{ GRAPH <gdb:vlist> 
            
            {{<nodeID:{0}> <rel:hasNodeType> <nodeType:{1}>}}}} 
            where {{

            }};

        """
        #print ADD_A_NODE_QUERY.format(nodeID)
        nodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', nodeID).strip()
        queryToExecute = ADD_A_NODE_QUERY.format(nodeID, nodeType)

        if execute == True:
            self.update(ADD_A_NODE_QUERY.format(nodeID, nodeType))

        if properties != None:
            queryToExecute+= self.add_node_properties(nodeID, properties, execute)

        if gdbinfo_update == True:
            self.update_outdegree_info()
            self.update_indegree_info()

        return queryToExecute

    def add_node_property(self, nodeID, key, val, forceToString = False, execute = True):
        
        ADD_A_PROPERTY_QUERY = """
            DELETE  {{
                GRAPH <gdb:vlist> {{<nodeID:{0}>  <property:{1}> ?any.}}
            }} WHERE 
            {{
                GRAPH <gdb:vlist> {{<nodeID:{0}>  <property:{1}> ?any.}}
            }}
            ;
            INSERT {{
                GRAPH <gdb:vlist> {{<nodeID:{0}>  <property:{1}> {2}.}}
            }}
            WHERE {{
               
            }};

        """
        nodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', nodeID)
        val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))

        if self.is_number(val)==False or forceToString==True:
            val = "\""+str(val)+"\""

        queryToExecute = ADD_A_PROPERTY_QUERY.format(nodeID, key, val)
        
        if execute==True:
            self.update(queryToExecute)

        return queryToExecute

    def add_node_unique_label_all_nodes(self, key, execute = True):

        ADD_LABELS = """
        insert {{graph <gdb:label> {{?s ?key ?str_s }}}} where {{
        select ?s (<label:{0}> as ?key) (STR(?s) as ?str_s) {{ graph <gdb:vlist> {{?s ?p ?o}}}}        
        }}
        """

        queryToExecute = ADD_LABELS.format(key)

        if execute==True:
            self.update(queryToExecute)

        return queryToExecute

    def add_node_label_all_nodes(self, key, val, forceToString = False, execute = True):

        ADD_LABELS = """
        insert {{graph <gdb:label> {{?s <label:{0}> {1} }}}} where {{
        select distinct ?s {{ graph <gdb:vlist> {{?s ?p ?o}}}}
        }}
        """

        val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))

        if self.is_number(val)==False or forceToString==True:
            val = "\""+str(val)+"\""

        queryToExecute = ADD_LABELS.format(key, val)
        
        if execute==True:
            self.update(queryToExecute)

        return queryToExecute

    def add_node_label(self, nodeID, key, val, forceToString = False, execute = True):
                
        ADD_LABEL_QUERY = """
            DELETE  {{
                GRAPH <gdb:label> {{<nodeID:{0}>  <label:{1}> ?any.}}
            }} WHERE 
            {{
                GRAPH <gdb:label> {{<nodeID:{0}>  <label:{1}> ?any.}}
            }}
            ;
            INSERT {{
                GRAPH <gdb:label> {{<nodeID:{0}>  <label:{1}> {2}.}}
            }}
            WHERE {{
               
            }};

        """
        nodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', nodeID)
        val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))

        if self.is_number(val)==False or forceToString==True:
            val = "\""+str(val)+"\""

        queryToExecute = ADD_LABEL_QUERY.format(nodeID, key, val)
        
        if execute==True:
            self.update(queryToExecute)

        return queryToExecute

    def update_outdegree_info(self, nodeID):
        QUERY_OUTDEGREE_UPDATE = """

        select (<nodeID:{0}> as ?s) (<rel:hasOutDegree> as ?rel) (count(*) as ?outdegree) 
        {{graph <gdb:topology> {{<nodeID:{0}> ?p ?o}}}}

        """
        nodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', nodeID)
        queryToExecute = QUERY_OUTDEGREE_UPDATE.format(nodeID)        
        self.update(queryToExecute)

    def update_indegree_info(self, nodeID):
        QUERY_INDEGREE_UPDATE = """

        select (<nodeID:{0}> as ?o) (<rel:hasInDegree> as ?rel) (count(*) as ?indegree) 
        {{graph <gdb:topology> {{?s ?p <nodeID:{0}>}}}}

        """
        nodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', nodeID)
        queryToExecute = QUERY_INDEGREE_UPDATE.format(nodeID)        
        self.update(queryToExecute)

    def update_outdegree_info_all(self):
        queryToExecute = """
        insert {graph <gdb:info> {?s ?rel ?outdegree}} where {
        select ?s (<rel:hasOutDegree> as ?rel) (count(*) as ?outdegree) 
        {graph <gdb:topology> {?s ?p ?o}} group by ?s
        }"""
        self.update(queryToExecute)

    def update_indegree_info_all(self):
        queryToExecute = """
        insert {graph <gdb:info> {?o ?rel ?indegree}} where {
        select ?o (<rel:hasInDegree> as ?rel) (count(*) as ?indegree) 
        {graph <gdb:topology> {?s ?p ?o}} group by ?o
        }"""
        self.update(queryToExecute)

    def add_node_properties(self, nodeID, properties, execute = True):
        queryToExecute = ""
        if properties ==True:
            return queryToExecute
        for key in properties.keys():
            queryToExecute += "\n"+ self.add_node_property(nodeID, key, properties[key], False, execute)
        return queryToExecute

    def add_edge(self, fromNodeID, toNodeID, edgeType=None, fromNodeType=None, toNodeType=None, properties = None, execute = True, create_node = False, bidirectional = False, noReturn = False, gdbinfo_update = False):
        
        queryToExecute = ""
        if create_node ==True:
            queryToExecute+="\n"+self.add_node(fromNodeID, fromNodeType, execute, gdbinfo_update = gdbinfo_update)
            queryToExecute+="\n"+self.add_node(toNodeID, toNodeType, execute, gdbinfo_update = gdbinfo_update)

        ADD_AN_EDGE_QUERY = """
        
            INSERT {{ GRAPH <gdb:topology> 
                
                {{?fromNodeID ?edgeID ?toNodeID}}}} 
                
                WHERE {{
                
                    SELECT 
                    (<nodeID:{0}> AS ?fromNodeID) 
                    (URI(CONCAT("edgeID:",str(?max))) AS ?edgeID) 
                    (<nodeID:{1}> AS ?toNodeID) WHERE {{
                    
                    {{GRAPH <gdb:info> {{<gdb:edgeIDCounter> <rel:equals> ?max}}}}
                
                }}              
            }};

            INSERT {{
                GRAPH <gdb:elist> {{?edgeID <rel:hasEdgeType> <edgeType:{2}>}}
            }}
            WHERE {{
               SELECT (URI(CONCAT("edgeID:",str(?count))) AS ?edgeID) 
               {{graph <gdb:info>{{<gdb:edgeIDCounter> <rel:equals> ?count.}}}}
            }};

            DELETE {{
                GRAPH <gdb:info> {{<gdb:edgeIDCounter> <rel:equals> ?count.}}
            }}
            INSERT {{
                GRAPH <gdb:info> {{<gdb:edgeIDCounter> <rel:equals> ?newcount.}}
            }}
            WHERE {{
               {{GRAPH <gdb:info>{{<gdb:edgeIDCounter> <rel:equals> ?count.}}}}
               BIND ((?count + 1) AS ?newcount)
            }};

        """

        fromNodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', fromNodeID).strip()
        toNodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', toNodeID).strip()
        queryToExecute +=ADD_AN_EDGE_QUERY.format(fromNodeID, toNodeID, edgeType)
        
        if bidirectional==True:
            queryToExecute +=ADD_AN_EDGE_QUERY.format(toNodeID, fromNodeID, edgeType)
    
        if execute == True:
            self.update(queryToExecute)

        if noReturn == False:
            GET_LAST_INSERTED_ID = """
            select ((?cnt-1) as ?lastID) {graph <gdb:info> {<gdb:edgeIDCounter> <rel:equals> ?cnt}}
            """
            results = self.query(GET_LAST_INSERTED_ID)
            
            for result in results['results']['bindings']:
                lastUpdatedID = int(result['lastID']['value'])
        else:
            lastUpdatedID = -1

        if properties != None:
            queryToExecute+= "\n"+ self.add_edge_properties(lastUpdatedID, properties, execute)

        addResult = {'query': queryToExecute, 'edgeId': lastUpdatedID}

        return addResult
        
     
    def add_edge_property(self, edgeID, key, val, forceToString = False, execute = True):

        ADD_A_PROPERTY_QUERY = """
            DELETE  {{
                GRAPH <gdb:elist> {{<edgeID:{0}>  <property:{1}> ?any.}}
            }} WHERE 
            {{
                GRAPH <gdb:elist> {{<edgeID:{0}>  <property:{1}> ?any.}}
            }}
            ;
            INSERT {{
                GRAPH <gdb:elist> {{<edgeID:{0}>  <property:{1}> {2}.}}
            }}
            WHERE {{
               
            }};

        """

        val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))

        if self.is_number(val)==False or forceToString==True:
            val = "\""+str(val)+"\""

        queryToExecute = ADD_A_PROPERTY_QUERY.format(edgeID, key, val)
        if execute ==True:
            self.update(queryToExecute)

        return queryToExecute

    def get_path(self, startNodeID, endNodeID, path_len=1):

        GET_PATH_HEADER = "?hop0_n"
        for i in range(1, path_len+1):
            GET_PATH_HEADER += " ?hop"+str(i)+" ?hop"+str(i)+"_n" 
        
        GET_PATH_HEAD = "select "+GET_PATH_HEADER+" {graph <gdb:topology> {\n"
        
        GET_PATH_TAIL = """}}

        filter (?hop0_n=<nodeID:{0}>)
        filter (?hop{2}_n=<nodeID:{1}>)

        }}"""

        GET_PATH_TAIL = GET_PATH_TAIL.format(startNodeID, endNodeID, path_len)

        if path_len <1:
            path_len = 1
        
        part_clause = "?hop{0}_n ?hop{1} ?hop{1}_n. \n"
        GET_PATH_BODY = GET_PATH_HEAD
        for i in range(0, path_len):
            GET_PATH_BODY+=part_clause.format(str(i), str(i+1))        
        GET_PATH_BODY+=GET_PATH_TAIL
        
        queryToExecute = GET_PATH_BODY

        results = self.query(queryToExecute)
        
        path_list = []
        for result in results['results']['bindings']:
            path = []            
            for i in range(0, path_len):
                startNode = str(result['hop'+str(i)+'_n']['value'])
                edgeID = str(result['hop'+str(i+1)]['value'])
                endNode = str(result['hop'+str(i+1)+'_n']['value'])
                path.append((startNode[7:],edgeID[7:],endNode[7:]))
            path_list.append(path)
        
        return path_list

    def get_edge(self, edgeID):
        
        GET_EDGE = """
        
        select ?rel ?val {{graph <gdb:elist> {{<edgeID:{0}> ?rel ?val}}}}

        """
        
        edgeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', edgeID).strip()
        queryToExecute = GET_EDGE.format(edgeID)
        
        results = self.query(queryToExecute)
        
        edge = {"edgeID": edgeID}

        for result in results['results']['bindings']:
            rel = str(result['rel']['value'])
            val = (result['val']['value'])
            if rel=='rel:hasEdgeType':
                edge["type"] = val[9:]
            else:
                if self.is_number(val)==True:
                    edge[rel[9:]] = float(val)
                else:
                    edge[rel[9:]] = str(val)
        return edge

    def get_label(self, nodeID, key):
        
        GET_LABEL = """
        
        select ?val {{graph <gdb:label> {{<nodeID:{0}> <label:{1}> ?val}}}}
        """
        queryToExecute = GET_LABEL.format(nodeID, key)
        #print queryToExecute
        results = self.query(queryToExecute)
        count = 0
        for result in results['results']['bindings']:
            val = str(result['val']['value'])
        
        return val
            
    def get_node_id_with_label(self, key, val = None, forceToString = False, limit = -1, offset = -1):
        
        GET_NODE = """
        
        select ?node {{graph <gdb:label> {{?node <label:{0}> {1}}}}}
        {LIMIT_CLAUSE}
        {OFFSET_CLAUSE}
        """
        
        if val == None:
            val = "?o"
        else:
            val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))
            if self.is_number(val)==False or forceToString==True:
                val = "\""+str(val)+"\""

        if limit <0:
            limitClause = ""
        else:
            limitClause = "LIMIT "+str(limit)

        if offset <0:
            offsetClause = ""
        else:
            offsetClause = "OFFSET "+str(offset)

        queryToExecute = GET_NODE.format(key, val, LIMIT_CLAUSE = limitClause, OFFSET_CLAUSE = offsetClause)
        #print queryToExecute
        results = self.query(queryToExecute)
        nodeIDs = []
        count = 0
        for result in results['results']['bindings']:
            nodeID = str(result['node']['value'])[7:]
            nodeIDs.append(nodeID)
           

        return nodeIDs

    def get_node(self, nodeID):
        
        GET_NODE = """
        
        select ?rel ?val {{graph <gdb:vlist> {{<nodeID:{0}> ?rel ?val}}}}

        """
        
        nodeID = re.sub('[^a-zA-Z0-9/_\\-:\\s]', '', nodeID).strip()
        queryToExecute = GET_NODE.format(nodeID)
        
        results = self.query(queryToExecute)
        
        node = {"nodeID": nodeID}

        for result in results['results']['bindings']:
            rel = str(result['rel']['value'])
            val = (result['val']['value'])
            if rel=='rel:hasNodeType':
                node["type"] = val[9:]
            else:
                if self.is_number(val)==True:
                    node[rel[9:]] = float(val)
                else:
                    node[rel[9:]] = str(val)
        return node
            
    def get_node_num(self, nodeType=None):
        
        if nodeType==None:
            nodeType ="?o"

        GET_LABEL_NUM = """
        
        select (count(*) as ?cnt) {{graph <gdb:vlist> {{?s <rel:hasNodeType> {0}}}}}

        """
        
        queryToExecute = GET_LABEL_NUM.format(nodeType)

        results = self.query(queryToExecute)
        
        for result in results['results']['bindings']:
            count = int(result['cnt']['value'])

        return count
    
    def get_label_num(self, key, val=None, nodeID=None, forceToString = False):
        
        if nodeID == None:
            nodeID = "?s"
        else:
            nodeID = "<nodeID:"+str(nodeID)+">"

        GET_LABEL_NUM = """
        
        select (count(*) as ?cnt) {{graph <gdb:label> {{{0} <label:{1}> {2}}}}}

        """

        if val == None:
            val = "?o"
        else:
            val = re.sub('[^a-zA-Z0-9\\-:.\\s]', '', str(val))
            if self.is_number(val)==False or forceToString==True:
                val = "\""+str(val)+"\""

        queryToExecute = GET_LABEL_NUM.format(nodeID, key, val)
        #print queryToExecute
        results = self.query(queryToExecute)
        
        for result in results['results']['bindings']:
            count = int(result['cnt']['value'])

        return count


    def add_edge_properties(self, edgeID, properties, execute = True):
        queryToExecute = ""
        if properties ==False:
            return queryToExecute        
        for key in properties.keys():
            queryToExecute += "\n"+self.add_edge_property(edgeID, key, properties[key], False, execute)      
        return queryToExecute

    # graph algorithms

    def get_node_ids_by_label_comparison(self, key_1, key_2, operand, limit = -1):
        
        LABEL_COMPARISON = """
                select ?s {{
        graph <gdb:label> {{?s <label:{0}> ?val_1}}
        graph <gdb:label> {{?s <label:{1}> ?val_2}}
        filter(?val_1 {2} ?val_2)
        }} 
        {LIMIT_CLAUSE}
        """

        if limit <0:
            limitClause = ""
        else:
            limitClause = "LIMIT "+str(limit)

        queryToExecute = LABEL_COMPARISON.format(key_1, key_2, operand, LIMIT_CLAUSE = limitClause)
        #print queryToExecute
        results = self.query(queryToExecute)
        nodeIDs = []
        count = 0
        for result in results['results']['bindings']:
            nodeID = str(result['s']['value'])[7:]
            nodeIDs.append(nodeID)
        
        return nodeIDs

    def store_labels_to_file(self, filePath, key, append = False, orderBy = 0):

        # 0 no sort
        # -1 desc sort
        # 1 asc sort

        mode = 'w'

        if append == True:
            mode = 'a'

        f = open(filePath, mode)
        
        resultNum = 0
        
        GET_LABEL_QUERY = """

        select ?s ?o {{graph <gdb:label> {{?s <label:{0}> ?o}} }}

        """
        
        if orderBy == 1:
            GET_LABEL_QUERY+= " order by ?o"
        
        elif orderBy == -1:
            GET_LABEL_QUERY+= " order by desc(?o)"

        queryToExecute = GET_LABEL_QUERY.format(key)
        results = self.query(queryToExecute)

        for result in results['results']['bindings']:
            s = str(result['s']['value'])
            o = str(result['o']['value'])
            resultNum += 1
            if (resultNum%100 ==0):
                print " - msg: "+str(resultNum)+" results written in file: "+ filePath

            f.write(s+"\t"+key+"\t"+o+"\n")

        print " - msg: "+str(resultNum)+" results written in file: "+ filePath

        f.close()

    # algorithms implemented using the API

    def personalized_pagerank(self, personalization, dampingFactor = 0.85, maxIteration = 50, toFile = False):
        print ""
        self.clear_labels_all() 
        print " - msg: Performing Personalized PageRank ..."
        numOfNodes = self.get_node_num()
        convergenceThreshold = 1.0 / float(numOfNodes) / 10.0 

        self.add_node_label_all_nodes("pagerank", 0)

        total = 0
        for key in personalization.keys():
            total+=float(personalization[key])

        for key in personalization.keys():
            self.add_node_label(str(key),"pagerank",float(personalization[key]/total));

        new_score_aggregation = "SUM(?label / ?outdegree) * {DAMPING_FACTOR} + {STAYING_FACTOR}"
        new_score_aggregation = new_score_aggregation.format(DAMPING_FACTOR = dampingFactor, STAYING_FACTOR = (1-dampingFactor)/float(numOfNodes))
        iteration_no = 0
        while True:
            startTime = time.time()
            print " - msg: iteration no: " + str(iteration_no)
            updated_no = self.aggregate_neighbor_labels("pagerank",nextKey = "pagerank", aggregateClause =new_score_aggregation, minDifference= convergenceThreshold)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if updated_no == 0 or iteration_no == maxIteration:
                break
            iteration_no+=1

        if toFile == True:
            filePath = "result/ppr_"+str(time.time()) + '.txt'
            self.store_labels_to_file(filePath, "pagerank", append = False, orderBy=-1)

    def pagerank(self, dampingFactor = 0.85, maxIteration = 50, toFile = False):
        print ""
        self.clear_labels_all() 
        print " - msg: Performing PageRank ..."
        numOfNodes = self.get_node_num()
        convergenceThreshold = 1.0 / float(numOfNodes) / 10.0 

        
        self.add_node_label_all_nodes("pagerank", float(1/float(numOfNodes)))
        new_score_aggregation = "SUM(?label / ?outdegree) * {DAMPING_FACTOR} + {STAYING_FACTOR}"
        new_score_aggregation = new_score_aggregation.format(DAMPING_FACTOR = dampingFactor, STAYING_FACTOR = (1-dampingFactor)/float(numOfNodes))
        iteration_no = 0
        while True:
            startTime = time.time()
            print " - msg: iteration no: " + str(iteration_no)
            updated_no = self.aggregate_neighbor_labels("pagerank",nextKey = "pagerank", aggregateClause =new_score_aggregation, minDifference= convergenceThreshold)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if updated_no == 0 or iteration_no == maxIteration:
                break
            iteration_no+=1

        if toFile == True:
            filePath = "result/pr_"+str(time.time()) + '.txt'
            self.store_labels_to_file(filePath, "pagerank", append = False, orderBy=-1)

    def connected_component(self, toFile = False):
        print ""
        self.clear_labels_all() 
        print " - msg: Performing Connected Component ..."
        self.add_node_unique_label_all_nodes("is_in_component")
        iteration_no = 0
        while True:
            startTime = time.time()     
            print " - msg: iteration no: " + str(iteration_no)
            updated_no = self.aggregate_neighbor_labels("is_in_component", aggregateClause = "min(?label)", includeItself = True)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if updated_no == 0:
                break
            iteration_no+=1

        if toFile == True:
            filePath = "result/cc_"+str(time.time()) + '.txt'
            self.store_labels_to_file(filePath, "is_in_component", append = False)
    
    def peer_pressure_clustering(self, toFile = False, maxIteration = 50):
        print ""
        self.clear_labels_all() 
        print " - msg: Performing Peer Pressure Clustering ..."

        iteration_no = 0
        self.add_node_unique_label_all_nodes("is_in_cluster")
        

        while True:
            startTime = time.time()     
            print " - msg: iteration no: " + str(iteration_no)
            updated_no = self.aggregate_neighbor_labels("is_in_cluster", aggregateClause = "voting", includeItself = True)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if updated_no == 0 or iteration_no == maxIteration:
                break

            iteration_no+=1

        if toFile == True:
            filePath = "result/pp_"+str(time.time()) + '.txt'
            self.store_labels_to_file(filePath, "is_in_cluster", append = False, orderBy=1)

    def single_source_shortest_path(self, startNodeID, maxIteration = 10, toFile = False):
        print ""
        self.clear_labels("distance") 
        print " - msg: Performing single source shortest path..."

        iteration_no = 0
        self.add_node_label_all_nodes("distance", 9999)
        self.add_node_label(startNodeID, "distance", iteration_no)
        while True:
            startTime = time.time()     
            print " - msg: iteration no: " + str(iteration_no)
            updated_no = self.aggregate_neighbor_labels("distance", aggregateClause = "min(?label+1)", includeItself = True, minDifference = -2)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if updated_no == 0 or iteration_no == maxIteration:
                break

            iteration_no+=1
            
        if toFile == True:
            filePath = "result/sspp_"+str(time.time()) + '.txt'
            self.store_labels_to_file(filePath, "distance", append = False, orderBy=1)
        
        return iteration_no

    def eccentricity(self, startNodeID, maxIteration = 10, toFile = False):
        print ""
        print " - msg: Computing eccentricity..."
        eccentricity = self.single_source_shortest_path(startNodeID, maxIteration, toFile = False)
        
        if toFile == True:
            filePath = "result/ec_"+str(time.time()) + '.txt'
            f = open(filePath, 'w')
            if eccentricity == maxIteration:
                eccentricity = "over > "+str(eccentricity)
            f.write("eccentricity = " + str(eccentricity)+"\n")
            print " - msg: The result (eccentricity = "+str(eccentricity)+") written in file: "+ filePath
            f.close()

        # returns eccentricity  
        return eccentricity

    def multi_source_shortest_path(self, startNodeID, endNodeID, maxIteration = 10, toFile = False):
        print ""
        self.clear_labels_all() 
        print " - msg: Performing multi source shortest path..."

        iteration_no = 0
        self.add_node_label_all_nodes("distance", 9999)
        self.add_node_label(startNodeID, "distance", iteration_no)
        while True:
            startTime = time.time()     
            print " - msg: iteration no: " + str(iteration_no)
            updated_no = self.aggregate_neighbor_labels("distance", aggregateClause = "min(?label+1)", includeItself = True, minDifference = -2)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if updated_no == 0 or iteration_no == maxIteration:
                distance = 9999
                break

            num_arrived_at_endNode =  self.get_label_num(nodeID=endNodeID, key="distance", val = iteration_no+1)
            if num_arrived_at_endNode >0:
                distance = iteration_no + 1
                break

            iteration_no+=1
            
        paths = []

        if distance > 0 and distance < 9999:
            paths = self.get_path(startNodeID, endNodeID, path_len=distance)
    
        if toFile == True:
            filePath = "result/mssp_"+str(time.time()) + '.txt'
            print " - msg: The shortest distance between two nodes ("+startNodeID+" and "+endNodeID+") = " +str(distance) + " written in file: "+ filePath
            f = open(filePath, 'w')
            f.write("distance between two nodes ("+startNodeID+" and "+endNodeID+") is :" +str(distance)+"\n")
            for path in paths:
                f.write(str(path)+"\n")
            f.close()

        return distance

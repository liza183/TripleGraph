# This functions are deprecated


    '''

    def multi_source_shortest_path(self, startNodeID, endNodeID, maxIteration = 10, toFile = False):
        print ""
        self.clear_labels() 
        print " - msg: Finding shortest paths (multi source)... "
        iteration_no = 0
        self.add_node_label(startNodeID, "marked", iteration_no)
        
        distance = 9999

        if startNodeID == endNodeID:
            distance = 0
        
        else:
            while True:
                startTime = time.time()    
                print " - msg: iteration no: " + str(iteration_no)
                self.propagate_label("marked", val = iteration_no, customPropagateClause="?value + 1")
                num_arrived_at_endNode =  self.get_label_num(nodeID=endNodeID, key="marked", val = iteration_no+1)
                if num_arrived_at_endNode >0:
                    distance = iteration_no + 1
                    break
                if iteration_no==maxIteration:
                    distance = 9999
                    break
                iteration_no+=1
                endTime = time.time()
                print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'

        print "The shortest distance between two nodes ("+startNodeID+" and "+endNodeID+") is :" +str(distance)
        
        paths = []

        if distance > 0 and distance < 9999:
            paths = self.get_path(startNodeID, endNodeID, path_len=distance)
    
        if toFile == True:
            filePath = "result/sp_"+str(time.time()) + '.txt'
            f = open(filePath, 'w')
            f.write("distance between two nodes ("+startNodeID+" and "+endNodeID+") is :" +str(distance)+"\n")
            for path in paths:
                f.write(str(path)+"\n")
            f.close()

        return distance

    def eccentricity(self, startNodeID, toFile = False, maxIteration = 10):
        print ""
        self.clear_labels()  
        print " - msg: Computing Eccentricy ... "
        iteration_no = 0
        self.add_node_label(startNodeID, "visited", iteration_no)
        visited_node_num_prev  = 0

        while True:
            startTime = time.time()            
            print " - msg: iteration no: " + str(iteration_no)
            self.propagate_label("visited", val = iteration_no, customPropagateClause="?value + 1")
            visited_node_num =  self.get_label_num(key="visited", val = iteration_no)
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            if iteration_no == maxIteration:
                eccentricity = iteration_no - 1
                iteration_no = -1
                break

            if visited_node_num == visited_node_num_prev:
                eccentricity = iteration_no - 1
                break
            else:
                visited_node_num_prev = visited_node_num
            
            iteration_no+=1


        if toFile == True:
            filePath = "result/ec_"+str(time.time()) + '.txt'
            f = open(filePath, 'w')
            if iteration_no == - 1:
                iteration_no = "over > "+str(eccentricity)
            f.write("eccentricity = " + str(eccentricity)+"\n")
            print " - msg: The result (eccentricity = "+str(eccentricity)+") written in file: "+ filePath
            f.close()

        return eccentricity

    def single_source_shortest_path_pa(self, startNodeID, maxIteration = 10, toFile = False):
        print ""
        self.clear_labels()  
        print " - msg: Finding shortest paths (single source)... "
        self.add_node_label_all_nodes("distance", 9999)
        iteration_no = 0
        self.add_node_label(startNodeID, "distance", iteration_no)
        while True:
            startTime = time.time()
            print " - msg: iteration no: " + str(iteration_no)
            self.propagate_label("distance", nextKey = "distance", val = iteration_no, customPropagateClause="?value + 1")
            self.aggregate_labels("distance", customAggregateClause="min(?label)")
            numNodesAtDistance =  self.get_label_num(key="distance", val = iteration_no)
            if numNodesAtDistance == 0 or iteration_no == maxIteration:
                break

            iteration_no+=1

            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'

        if toFile == True:
            filePath = "result/sssp_"+str(time.time()) + '.txt'
            f = open(filePath, 'w')
            f.write("single source shortest path from node: " + str(startNodeID)+"\n\n")
            f.close()
            self.store_labels_to_file(filePath, "distance", append = True, orderBy=1)

    # this function is deprecated
    def aggregate_neighbor_labels(self, key, aggkey,customAggregateClause):

        AGG_NEIGHBOR_QUERY = """
        
        insert  {{ graph <gdb:label> {{?v <label:{1}> ?aggLabel }}  }} 
        where {{

            {{
                select ?v ({2} as ?aggLabel) {{
                {{select ?v {{graph <gdb:vlist> {{?v ?p ?o}}}}}}
                {{graph <gdb:label> {{?neighbor <label:{0}> ?label}}}}
                {{graph <gdb:topology> {{?v ?edge ?neighbor}}}}}} 
                group by ?v
            }}
        }}

        """

        queryToExecute = AGG_NEIGHBOR_QUERY.format(key, aggkey,customAggregateClause)
        self.connection.urika.update(self.name, queryToExecute)

    def aggregate_labels_voting(self, key, nextKey = None):

        if nextKey == None:
            nextKey = key

        AGGREGATE_LABEL = """
            

        insert {{graph <gdb:tmp> {{?node ?tmp_label ?cnt}}}} where {{
        select ?node (URI(CONCAT(str(?label))) AS ?tmp_label) ?cnt
        where {{
        {{ select ?node ?label (count(?label) as ?cnt) 
          {{graph <gdb:label> {{?node <label:{0}> ?label}}}} group by ?node ?label}}
        }}
        }};

        delete {{graph <gdb:label> {{?node <label:{0}> ?original}}}}
        insert {{graph<gdb:label> {{?node <label:{1}> ?reduced}}}} 
        where {{

            {{graph <gdb:label> {{?node <label:{0}> ?original}}}}
           
            {{
                select ?node (str(min(?label)) as ?reduced)
                {{
                {{
                select ?node (max(?cnt) as ?maxCnt)
                {{select * {{graph <gdb:tmp> {{?node ?label ?cnt}}}}}} 
                group by ?node
                }}
                {{
                select ?node ?label ?cnt {{graph <gdb:tmp> {{?node ?label ?cnt}}}}
                }}
                filter(?cnt = ?maxCnt)
                }} group by ?node
            }}
        }}

        """
        queryToExecute = AGGREGATE_LABEL.format(key, nextKey)
        print queryToExecute
        
        self.connection.urika.update(self.name, queryToExecute)

    def peer_pressure_clustering(self, toFile = False, maxIteration = 50):
        print ""
        self.clear_labels() 
        print " - msg: Performing Peer-Pressure Clustering ..."

        iteration_no = 0
        self.add_node_unique_label_all_nodes("is_in_cluster:iter:"+str(iteration_no))

        while True:
            startTime = time.time()
            print " - msg: iteration no: " + str(iteration_no)
            self.propagate_label("is_in_cluster:iter:"+str(iteration_no), nextKey = "is_in_cluster:iter:"+str(iteration_no+1), customPropagateClause="?value")
            self.aggregate_labels_voting("is_in_cluster:iter:"+str(iteration_no+1))
            
            if iteration_no == maxIteration:
                break

            iteration_no+=1
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'

        if toFile == True:
            filePath = "result/pp_"+str(time.time()) + '.txt'
            self.store_labels_to_file(filePath, "is_in_cluster:iter:"+str(iteration_no+1), append = False, orderBy=1)

    def eccentricity(self, startNodeID, toFile = False, maxIteration = 10):
        self.clear_labels()
        print " - msg: Computing Eccentricy ... "
        iteration_no = 0
        self.add_node_label(startNodeID, "distance", iteration_no)
        visited_node_num_prev  = 0
       
        while True:
            startTime = time.time()
            print " - msg: iteration no: " + str(iteration_no)
            s = raw_input("")
            
            self.aggregate_neighbor_labels("distance", includeItself = False, customAggregateClause ="min(?label +1)", minDifference = -1, noReturn = True)
            visited_node_num =  self.get_label_num(key="distance")
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            
            if iteration_no == maxIteration:
                iteration_no = -1
                break
                            
            if visited_node_num == visited_node_num_prev:
                break
            else:
                visited_node_num_prev = visited_node_num
            
            iteration_no+=1
            
        if toFile == True:
            filePath = "result/ec_"+str(time.time()) + '.txt'
            f = open(filePath, 'w')
            if iteration_no == - 1:
                iteration_no = "over > "+str(maxIteration)
            f.write("eccentricity = " + str(iteration_no)+"\n")
            print " - msg: The result (eccentricity = "+str(iteration_no)+") written in file: "+ filePath
            f.close()    

        return iteration_no

    def connected_component_pa(self, toFile = False):
        print ""
        self.clear_labels() 
        print " - msg: Performing Connected Component ..."
        self.add_node_unique_label_all_nodes("is_in_cluster:0")
        iteration_no = 0
        while True:
            startTime = time.time()
            print " - msg: iteration no: " + str(iteration_no)
            self.propagate_label("is_in_cluster:"+str(iteration_no), nextKey = "is_in_cluster:"+str(iteration_no+1), customPropagateClause="?value", includeItself = True)
            self.aggregate_labels("is_in_cluster:"+str(iteration_no+1), customAggregateClause="min(?label)")
            print self.get_label_num(key="is_in_cluster:"+str(iteration_no+1))
            ss = raw_input()
            endTime = time.time()
            print ' - msg: Elapsed Time: ' + str(endTime - startTime) + ' seconds.'
            iteration_no+=1

    '''

    
    '''

    # too slow to be used
    
    def bounding_eccentricities(self):
        print ""
        print " - msg: Computing bounding eccentrities..."
        
        self.clear_labels("upper")
        self.clear_labels("lower")
        self.clear_labels("lower_1")
        self.clear_labels("lower_2")

        self.add_node_label_all_nodes("upper", 9999)
        self.add_node_label_all_nodes("lower_1", -9999)
        self.add_node_label_all_nodes("lower_2", 9999)
        self.add_node_label_all_nodes("lower", -9999)

        super_step_no = 0
        while True:
            print " - msg: super step no: " + str(super_step_no)
            nodeID = self.get_node_ids_by_label_comparison("upper","lower","!=", limit=1)
            if len(nodeID) == 0:
                break

            self.eccentricity_bounder(nodeID[0])
            super_step_no+=1
            
        #print eccentricity

    def eccentricity_bounder(self, nodeID):

        print " - msg : Updating lower/upper bounds ..."
        eccentricity = self.single_source_shortest_path(nodeID, 20, toFile = False)
        self.clear_labels("distance")

        self.add_node_label(nodeID, "eccentricity", eccentricity)
        self.add_node_label(nodeID, "upper", eccentricity)
        self.add_node_label(nodeID, "lower_1", eccentricity)
        self.add_node_label(nodeID, "lower_2", 0)

        # upper bound

        while True:
            updated_no = self.aggregate_neighbor_labels("upper", aggregateClause = "min(?label+1)", includeItself = False, minDifference = -2)
            if updated_no == 0:
                break

        # lower bound
        while True:
            updated_no = self.aggregate_neighbor_labels("lower_1", aggregateClause = "max(?label-1)", includeItself = False, minDifference = -1)
            if updated_no == 0:
                break

        while True:
            updated_no = self.aggregate_neighbor_labels("lower_2", aggregateClause = "min(?label+1)", includeItself = False, minDifference = -2)
            if updated_no == 0:
                break

        self.copy_node_label("lower_1","lower")
        self.clear_labels("lower_2", 9999)
        self.copy_node_label("lower_2","lower")
        self.aggregate_labels("lower", customAggregateClause="max(?label)")
    '''
    
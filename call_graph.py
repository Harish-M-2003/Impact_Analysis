from typing import Dict, List, Optional
from json import loads
import networkx as nx
from repo_orchestrator import GitRepo


class CallGraph:

    def __init__(self, delta_changes):
        
        self.__graph = nx.DiGraph()
        self.__initialize_graph_with(delta_changes)
        
    def __initialize_graph_with(self, delta_changes):

        for file in delta_changes:
            for change in file.changed_methods:
                node = {
                    "file_path" : None,
                    "function_name" : change.name[change.name.find("::") + 2:],
                    "parameters" : change.parameters,
                    "class_name" : change.name[:change.name.find(":")],
                    "start_line_no" : change.start_line,
                    "end_line_no" : change.end_line,
                    "is_changed" : True
                }

                self.add_node(**node)

    def get_graph(self):

        return self.__graph

    def add_node(self, **node):

        if node is None:
            raise ValueError("Node cannot be None")

        self.__graph.add_node(
            node["class_name"] + "::" + node["function_name"] + str(node["parameters"]),
            file_path=node["file_path"],
            class_name=node["class_name"],
            start_line_no= node["start_line_no"],
            end_line_no= node["end_line_no"],
            is_changed= node["is_changed"],
            parameters= node["parameters"],
            function_name= node["function_name"] 
        )

    def add_edge(self, caller, callee):

        if caller is None or callee is None:
            raise ValueError("Valid nodes required")


        if not self.__graph.has_node(caller) or not self.__graph.has_node(callee):
            raise ValueError("Both nodes must exist before adding edge")

        self.__graph.add_edge(caller, callee)

    def get_node(self, function_name: str) -> Optional[Dict]:

        if not self.__graph.has_node(function_name):
            return None

        return self.__graph.nodes[function_name]

    def get_callees(self, function_name: str) -> List[Dict]:

        return [
            self.__graph.nodes[n]
            for n in self.__graph.successors(function_name)
        ]

    def get_callers(self, function_name: str) -> List[Dict]:

        return [
            self.__graph.nodes[n]
            for n in self.__graph.predecessors(function_name)
        ]

    def get_impacted_nodes(self, function_name: str) -> List[Dict]:

        visited = set()

        def dfs(node):
            for parent in self.__graph.predecessors(node):
                if parent not in visited:
                    visited.add(parent)
                    dfs(parent)

        dfs(function_name)

        return [
            self.__graph.nodes[n]
            for n in visited
        ]

    def print_nodes(self):

        for node, data in self.get_graph().nodes(data=True):
            print("\nNODE:", node)
            for k, v in data.items():
                print(f"  {k}: {v}")

    def get_parameters(self, edge_meta_data):

        parameter_map = {}

        for row in edge_meta_data:

            caller = row[0]["label"]
            impl = row[1]["label"]

            caller_class = row[4]
            impl_class = row[5]

            caller_param = row[6]["label"]
            impl_param = row[7]["label"]

            caller_key = f"{caller_class}::{caller}"
            impl_key = f"{impl_class}::{impl}"

            parameter_map.setdefault(caller_key, set()).add(caller_param)
            parameter_map.setdefault(impl_key, set()).add(impl_param)

        return parameter_map

    
    def enrich(self, affected_flows):

        """
        {'#select': { 'tuples': [
            [{'label': 'A'}, {'label': 'B'}, 'src/main/java/com/example/demo/controllers/DemoController.java', class_name, start_line, end_line], 
            [{'label': 'B'}, {'label': 'C'}, 'src/main/java/com/example/demo/controllers/DemoController.java', 29], 
            [{'label': 'C'}, {'label': 'D'}, 'src/main/java/com/example/demo/utils/Tool.java', 14], 
            [{'label': 'F'}, {'label': 'A'}, 'src/main/java/com/example/demo/controllers/DemoController.java', 35], 
            [{'label': 'D'}, {'label': 'E'}, 'src/main/java/com/example/demo/utils/Tool.java', 18]
            ]}
        }
        """

        flows = loads(affected_flows)

        edges = flows['#select']['tuples']

        parameters = self.get_parameters(edges)

        for edge in edges:
            
            source_file_path= edge[2]
            source_class_name= edge[4]
            source_start_line_no= edge[8]
            source_end_line_no= edge[10]
            source_node= edge[0]['label']
            source_parameters= list(parameters[source_class_name + "::" + source_node])
            source=  source_class_name + "::" + source_node + str(source_parameters)

            target_file_path= edge[3]
            target_class_name= edge[5]
            target_start_line_no= edge[9]
            target_end_line_no= edge[11]
            target_node= edge[1]['label'] 
            target_parameters= list(parameters[target_class_name + "::" + target_node])
            target= target_class_name + "::" + target_node + str(target_parameters) 

            if source in self.__graph: #Need to change source_node
                
                node = self.get_node(source)

                if not node["file_path"]:
                    node["function_name"]= source_node
                    node["file_path"]= source_file_path
                    node["class_name"]= source_class_name
                    node["start_line_no"]= source_start_line_no
                    node["end_line_no"]= source_end_line_no
                    node["parameters"]= source_parameters
            else:                

                self.add_node(
                        file_path=source_file_path,
                        function_name=source_node,
                        start_line_no=source_start_line_no,
                        end_line_no=source_end_line_no,
                        class_name=source_class_name,
                        is_changed=False,
                        parameters=source_parameters
                )

            if target in self.__graph:
                
                node = self.get_node(target)

                if not node["file_path"]:
                    node["function_name"]= target_node
                    node["file_path"]= target_file_path
                    node["class_name"]= target_class_name
                    node["start_line_no"]= target_start_line_no
                    node["end_line_no"]= target_end_line_no
                    node["parameters"]= target_parameters
                    # from codeql we are getting the start_line_no for the caller function, so temporary comment this line
                    # node["start_line_no"]= start_line_no
                    # node["end_line_no"]= end_line_no
            else:
                self.add_node(
                        file_path=target_file_path,
                        function_name=target_node,
                        start_line_no=target_start_line_no,
                        end_line_no=target_end_line_no,
                        class_name=target_class_name,
                        is_changed=False,
                        parameters=target_parameters
                )

            self.__graph.add_edge(source, target)



if __name__ == "__main__":

    data = """
    {"#select":{"columns":[
   {"name":"caller","kind":"Entity"}
  ,{"name":"impl","kind":"Entity"}
  ,{"kind":"String"}
  ,{"kind":"String"}
  ,{"kind":"String"}
  ,{"kind":"String"}
  ,{"kind":"Entity"}
  ,{"kind":"Entity"}
  ,{"kind":"Integer"}
  ,{"kind":"Integer"}
  ,{"kind":"Integer"}
  ,{"kind":"Integer"}]
 ,"tuples":[
   [{"label":"createStudent"},{"label":"createStudent"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/controller/StudentController.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","StudentController","StudentServiceImpl",{"label":"student"},{"label":"student"},28,19,28,19]
  ,[{"label":"updateStudent"},{"label":"updateStudent"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/controller/StudentController.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","StudentController","StudentServiceImpl",{"label":"id"},{"label":"id"},55,31,55,31]
  ,[{"label":"updateStudent"},{"label":"updateStudent"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/controller/StudentController.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","StudentController","StudentServiceImpl",{"label":"id"},{"label":"student"},55,31,55,31]
  ,[{"label":"updateStudent"},{"label":"updateStudent"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/controller/StudentController.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","StudentController","StudentServiceImpl",{"label":"student"},{"label":"id"},55,31,55,31]
  ,[{"label":"updateStudent"},{"label":"updateStudent"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/controller/StudentController.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","StudentController","StudentServiceImpl",{"label":"student"},{"label":"student"},55,31,55,31]
  ,[{"label":"deleteStudent"},{"label":"deleteStudent"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/controller/StudentController.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","StudentController","StudentServiceImpl",{"label":"id"},{"label":"id"},71,37,71,37]
  ,[{"label":"updateStudent"},{"label":"setId"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/entity/Student.java","StudentServiceImpl","Student",{"label":"id"},{"label":"id"},31,22,31,22]
  ,[{"label":"updateStudent"},{"label":"setId"},"C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/service/StudentServiceImpl.java","C:/Users/pooja/Desktop/Spring-Boot-REST-API/Spring-Boot-REST-API/src/main/java/com/wasim/rest/api/entity/Student.java","StudentServiceImpl","Student",{"label":"student"},{"label":"id"},31,22,31,22]]
 }}
    """

    json_data = loads(data)

    repo_path = r'C:\\Users\\pooja\\Desktop\\Spring-Boot-REST-API'
    commit_hash = 'dcc8905ebec19346491acab56a14a72f498126e5'

    delta_files= GitRepo(repo_path, commit_hash).get_changed_methods()

    CallGraph(delta_files).get_parameters(json_data['#select']['tuples'])
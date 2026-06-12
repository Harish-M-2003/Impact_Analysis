import ast
import os
import networkx as nx
import subprocess
import re


class DependencyVisitor(ast.NodeVisitor):

    def __init__(self, graph, file_name):
        self.graph = graph
        self.file_name = file_name
        self.current_function = None

    def visit_FunctionDef(self, node):

        function_name = node.name

        self.graph.add_node(
            function_name,
            type="function",
            file=self.file_name
        )

        self.current_function = function_name

        self.generic_visit(node)

    def visit_Call(self, node):

        if self.current_function:

            if isinstance(node.func, ast.Name):

                callee = node.func.id

                self.graph.add_edge(
                    self.current_function,
                    callee,
                    relation="CALLS"
                )

        self.generic_visit(node)

def build_graph(root_folder):

    graph = nx.DiGraph()

    for root, _, files in os.walk(root_folder):

        for file in files:

            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            with open(path, "r") as f:
                source = f.read()

            try:

                tree = ast.parse(source)

                visitor = DependencyVisitor(
                    graph,
                    path
                )

                visitor.visit(tree)

            except Exception as ex:
                print("Parse error:", path, ex)

    return graph

def find_impacted_functions(graph, changed_function):

    return nx.ancestors(
        graph,
        changed_function
    )

def get_tests(graph):

    tests = []

    for node in graph.nodes:

        if str(node).startswith("test_"):
            tests.append(node)

    return tests

def find_impacted_tests(graph, changed_function):

    impacted = set()

    reverse_graph = graph.reverse()

    stack = [changed_function]

    visited = set()

    while stack:

        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        for parent in reverse_graph.neighbors(current):

            if parent.startswith("test_"):
                impacted.add(parent)

            stack.append(parent)

    return impacted

def print_graph(graph):

    print("\nDEPENDENCIES")

    for source, target, data in graph.edges(data=True):

        print(
            f"{source} --{data['relation']}--> {target}"
        )

def get_git_diff():

    result = subprocess.run(
        ["git", "diff", "HEAD~1"],
        capture_output=True,
        text=True
    )

    return result.stdout

def changed_functions_from_diff(diff):

    functions = []

    pattern = r"def\s+(\w+)\("

    for line in diff.splitlines():

        if line.startswith("+"):

            match = re.search(
                pattern,
                line
            )

            if match:
                functions.append(
                    match.group(1)
                )

    return functions

def calculate_risk(
        impacted_functions,
        impacted_tests):

    score = 0

    score += len(impacted_functions) * 2

    score += len(impacted_tests) * 3

    return min(score, 10)


if __name__ == "__main__":

    graph = build_graph(".")

    print_graph(graph)

    changed_function = changed_functions_from_diff(get_git_diff())

    impacted = find_impacted_functions(
        graph,
        changed_function
    )

    tests = find_impacted_tests(
        graph,
        changed_function
    )

    print("\nChanged Function:")
    print(changed_function)

    print("\nImpacted Functions:")
    for func in impacted:
        print("-", func)

    print("\nRecommended Tests:")
    for test in tests:
        print("-", test)
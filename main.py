
from repo_orchestrator import GitRepo
from codeql import CodeQL
from call_graph import CallGraph

from enums.LanguageSupported import LanguageSupported
from pathlib import Path

repo_path = r'C:\\Users\\pooja\\Desktop\\Spring-Boot-REST-API'
commit_hash = 'dcc8905ebec19346491acab56a14a72f498126e5'

SYSTEM_PROMT= """
You are an expert code impact analysis and test optimization assistant.

You will be given:
1. A list of impacted execution flows (methods and call paths affected by code changes)
2. The existing test cases in the system

Your task is to determine which existing test cases are sufficient to validate the impacted flows and which additional tests (if any) are required.

Focus on:
- Mapping impacted flows to existing test coverage
- Identifying redundant or unnecessary test execution
- Highlighting missing test coverage for impacted paths
- Ensuring critical and high-risk flows are fully validated

Do NOT suggest testing everything.

Instead:
- Optimize test selection
- Reduce redundant test execution
- Prioritize tests that cover changed methods and their upstream/downstream impact

Output format:
- Required tests (must run)
- Optional tests (nice to run if time permits)
- Missing tests (must be added)
- Reasoning mapped to impacted flows
"""

delta_files= GitRepo(repo_path, commit_hash).get_changed_methods()

graph = CallGraph(delta_files)

codeql= CodeQL(
    Path(repo_path + "\\Spring-Boot-REST-API"),
    "example",
    LanguageSupported.JAVA
)

impact= codeql.get_impact(graph)

graph.enrich(impact)

graph.print_nodes()

for k,v in graph.get_graph().adjacency():
    print(k , v)

# graph.print_nodes()
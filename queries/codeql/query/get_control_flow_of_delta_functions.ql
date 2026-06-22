import java

external predicate targetMethodName(string name);

predicate isTarget(Method m) {
  exists(string name |
    targetMethodName(name) and
    m.hasName(name)
  )
}

from Method m, ControlFlowNode src, ControlFlowNode dst
where
  isTarget(m) and
  src.getEnclosingCallable() = m and
  dst.getEnclosingCallable() = m and
  src.getASuccessor() = dst
select
  m.getDeclaringType().getName(),
  m.getName(),
  src.toString(),
  dst.toString(),
  src.getLocation().getStartLine(),
  dst.getLocation().getStartLine()
// Need to enhance this query to get downstreams which got impacted

import java

external predicate targetMethodName(string name);

predicate isTarget(Method m) {
  exists(string name |
    targetMethodName(name) and
    m.hasName(name)
  )
}
predicate directCall(Method caller, Method callee) {
  exists(Call c |
    c.getEnclosingCallable() = caller and
    c.getCallee() = callee
  )
}

predicate directCallEdge(Method caller, Method callee, Call c) {
  c.getEnclosingCallable() = caller and
  c.getCallee() = callee
}

predicate concreteImpl(Method base, Method impl) {
  impl.overrides*(base) and
  not impl.getDeclaringType() instanceof Interface
}

// predicate resolvesToImpl(Method m, Method impl) {
//   impl.overrides*(m)
// }

from Method caller, Method callee, Method target, Method impl, Call c, Parameter p
where
  isTarget(target) and
  directCallEdge(caller, callee, c) and
  directCall*(callee, target) and
  concreteImpl(callee, impl) and
  p.getCallable() = caller
select
  caller,
  impl,
  caller.getFile().getAbsolutePath(),
  // callee.getFile().getAbsolutePath(),
  impl.getDeclaringType().getFile().getAbsolutePath(),
  caller.getDeclaringType().getName(),
  impl.getDeclaringType().getName(),
  caller.getAParameter(),
  impl.getAParameter(),
  caller.getLocation().getStartLine(),
  impl.getLocation().getStartLine(),
  caller.getLocation().getEndLine(),
  impl.getLocation().getEndLine()
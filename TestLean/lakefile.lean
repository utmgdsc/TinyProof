import Lake
open Lake DSL

require REPL from git "https://github.com/leanprover-community/repl.git" @ "master"

package «TestLean» where
  -- Package version
  version := v!"0.1.0"

@[default_target]
lean_lib «TestLean» where
  -- Library configuration options can be added here

import TestLean

def main : IO Unit :=
  IO.println s!"Hello, {hello}!"

theorem womp1 (a b : Nat) : a + b + c = c + (b + a) := by
  rw [Nat.add_comm, Nat.add_comm a b]

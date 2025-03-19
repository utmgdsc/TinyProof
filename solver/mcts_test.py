import os
import subprocess
import json

counter = 0
def generate(s):
  global counter
  if counter == 0:
    counter += 1
    return "example (a b c : Nat): c + a + b = a + (b + c) := by\n  cases a with\n  | zero => "
  return "example (a b c : Nat): c + a + b = a + (b + c) := by\n  rw [Nat.add_comm]\n  rw [<- Nat.add_assoc]"

def count_leading_whitespace(s):
    return len(s) - len(s.lstrip())

# TODO :: support adding mutiple goals
def addGoal(ctx, pos, goal):
  # note: line numbers start at 1
  whitespace = count_leading_whitespace(ctx.split("\n")[pos["line"] - 1])
  out = ctx + "\n" + whitespace * " " + "/-\n"
  lines = goal.split("\n")
  for line in lines:
    out += whitespace * " " + line + "\n"
  out += whitespace * " " + "-/"
  return out

HOME_DIR = os.path.expanduser('~')
DEFAULT_LAKE_PATH = f'{HOME_DIR}/.elan/bin/lake'
DEFAULT_LEAN_WORKSPACE = 'TestLean'
i = 0

messages = []

prompt = "example (a b c : Nat): c + a + b = a + (b + c) := by"
while messages != None:
  if i == 2:
    exit()
  temp = generate(prompt)
  # Create a proper JSON command for the Lake REPL
  repl_command = { "cmd" : temp }

  print(prompt)

  # Convert the command to JSON string
  json_input = json.dumps(repl_command)

  # Run the Lake REPL and pipe the JSON input directly
  process = subprocess.run(
      [DEFAULT_LAKE_PATH, "exe", 'repl'],
      input=json_input,
      capture_output=True,
      text=True,
      cwd=DEFAULT_LEAN_WORKSPACE,
      timeout=300
  )

  print(process.stderr)
  print(process.stdout)
  output = json.loads(process.stdout)
  print(output)
  prompt = addGoal(temp, output.get("messages")[0]["pos"], output.get("messages")[0]["data"])

  print("Return code:", process.returncode)
  print("Stdout:", process.stdout)
  # print("Stderr:", process.stderr)
  i += 1

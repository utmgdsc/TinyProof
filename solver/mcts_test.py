import os
import subprocess
import json

counter = 0
def generate(s):
  global counter
  out = ["example (a b c : Nat): c + a + b = a + (b + c) := by\n  cases a with\n  | zero => ", "example (a b c : Nat): c + a + b = a + (b + c) := by\n  rw [Nat.add_assoc] ", "example (a b c : Nat): c + a + b = a + (b + c) := by\n  rw [Nat.add_assoc]\n  rw [<- Nat.add_comm]\n  rw [Nat.add_assoc]"][counter]
  counter += 1
  return out

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

def getLastTacticNode(infoTree):
    curr = infoTree
    while len(curr["children"]) != 0:
        curr = curr["children"][-1]
    return curr

def getErrors(msgs):
    return list(filter(lambda o: o["severity"] == "error", msgs))

HOME_DIR = os.path.expanduser('~')
DEFAULT_LAKE_PATH = f'{HOME_DIR}/.elan/bin/lake'
DEFAULT_LEAN_WORKSPACE = 'TestLean'

prompt = "example (a b c : Nat): c + a + b = a + (b + c) := by"
while True:
  temp = generate(prompt)
  # Create a proper JSON command for the Lake REPL
  repl_command = { "cmd" : temp, "infotree": "tactics" }

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

  print("stderr:", process.stderr)
  # print("stdout:", process.stdout)
  output = json.loads(process.stdout)
  # print(output)
  messages = output.get("messages")
  if messages is None or len(getErrors(messages)) == 0:
    break
  node = getLastTacticNode(output["infotree"][0])
  prompt = addGoal(temp, node['node']['stx']['range']['finish'], node['node']['goalsBefore'][0])
  # print("Stderr:", process.stderr)

import os
import subprocess
import json
from typing import Generator

HOME_DIR = os.path.expanduser('~')
DEFAULT_LAKE_PATH = f'{HOME_DIR}/.elan/bin/lake'

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEAN_WORKSPACE = f'{PARENT_DIR}/TestLean'

print(f'DEFAULT_LAKE_PATH: {DEFAULT_LAKE_PATH}')
print(f'DEFAULT_LEAN_WORKSPACE: {DEFAULT_LEAN_WORKSPACE}')


def generate(s: str, counter: int) -> str:
    out: list[str] = [
        "example (a b c : Nat): c + a + b = a + (b + c) := by\n  cases a with\n  | zero => ",
        "example (a b c : Nat): c + a + b = a + (b + c) := by\n  rw [Nat.add_assoc] ",
        "example (a b c : Nat): c + a + b = a + (b + c) := by\n  rw [Nat.add_assoc]\n  rw [<- Nat.add_comm]\n  rw [Nat.add_assoc]"
    ]

    return out[counter]


def count_leading_whitespace(s: str) -> int:
    return len(s) - len(s.lstrip())


def add_goal(ctx: str, pos: dict, goal: str) -> str:
    # note: line numbers start at 1
    whitespace = count_leading_whitespace(ctx.split("\n")[pos["line"] - 1])
    out = ctx + "\n" + whitespace * " " + "/-\n"
    lines = goal.split("\n")
    for line in lines:
        out += whitespace * " " + line + "\n"
    out += whitespace * " " + "-/"
    return out


def get_last_tactic_node(info_tree: dict) -> dict:
    curr = info_tree
    while len(curr["children"]) != 0:
        curr = curr["children"][-1]
    return curr


def get_errors(msgs: list[dict]) -> list[dict]:
    return list(filter(lambda o: o["severity"] == "error", msgs))


def do_work(prompt: str) -> Generator[str, None, None]:

    yield prompt

    counter: int = 0
    while True:
        temp = generate(prompt, counter)
        counter += 1

        # Create a proper JSON command for the Lake REPL
        repl_command = {"cmd": temp, "infotree": "tactics"}

        # Convert the command to JSON string
        json_input = json.dumps(repl_command)

        # Run the Lake REPL and pipe the JSON input directly
        try:
          process = subprocess.run(
              [DEFAULT_LAKE_PATH, "exe", 'repl'],
              input=json_input,
              capture_output=True,
              text=True,
              cwd=DEFAULT_LEAN_WORKSPACE,
              timeout=300
          )
        except subprocess.SubprocessError as e:
          print(f"Error running subprocess: {e}")
          yield f"Subprocess failed: {e}"
          break

        if process.returncode != 0:
            yield f"Lake error: \n{process.stderr}"
            break
            
        # yield process.stderr

        try:
          output = json.loads(process.stdout)
        except:
            yield f"Invalid JSON from Lean:\n{process.stdout}"
            break
        messages = output.get("messages")

        if messages is None or len(get_errors(messages)) == 0:
            break

        node = get_last_tactic_node(output["infotree"][0])
        yield temp
        # prompt = add_goal(
        #     temp, node['node']['stx']['range']
        #     ['finish'], node['node']['goalsBefore'][0]
        # )


if __name__ == "__main__":
    for prompt in do_work("example (a b c : Nat): c + a + b = a + (b + c) := by"):
        print(prompt)

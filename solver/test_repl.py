import os
import subprocess
import json
import time
import sys

HOME_DIR = os.path.expanduser('~')
DEFAULT_LAKE_PATH = f'{HOME_DIR}/.elan/bin/lake'
DEFAULT_LEAN_WORKSPACE = 'TestLean'

process = subprocess.Popen(
        [DEFAULT_LAKE_PATH, "exe", "repl"],  # Replace with your target executable
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="TestLean",
        text=True,
        bufsize=1,
        env=os.environ,  # Inherit environment variables
        preexec_fn=os.setsid if sys.platform != 'win32' else None,
    )

def send_json_command(command):
    """Send JSON command and read response from subprocess."""
    json_input = json.dumps(command, ensure_ascii=False) + "\n\n"
    
    process.stdin.write(json_input)
    process.stdin.flush()  # Ensure input is sent
        
    output_lines = []
    while True:
        line = process.stdout.readline().strip()
        if not line:  # Stop reading when there's no more output
            break
        output_lines.append(line)
    
    return "\n".join(output_lines)

def getLastTacticNode(infoTree):
    curr = infoTree
    while len(curr["children"]) != 0:
        curr = curr["children"][-1]
    return curr

def getErrors(msgs):
    return list(filter(lambda o: o["severity"] == "error", msgs))

repl_command = { "cmd": "theorem womp (a b c : Nat) : (a + b) + c = c + a + b := by ", "infotree": "tactics" }

stdout = send_json_command(repl_command)
# print(f"stdout: {stdout}")
output = json.loads(stdout)
# print(output)
print(getLastTacticNode(output["infotree"][0]))
print(getErrors(output["messages"]))
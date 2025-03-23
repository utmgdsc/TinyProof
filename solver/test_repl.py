import os
import subprocess
import json
import time

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
        preexec_fn=os.setsid,
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

repl_command = { "cmd": "theorem womp (a b c : Nat) : (a + b) + c = c + a + b := by sorry" }

stdout = send_json_command(repl_command)
print(f"stdout: {stdout}")

repl_command = { "tactic": "(\n rw [Nat.add_comm]\n rw [<- Nat.add_assoc])", "proofState": 0 }
json_input = json.dumps(repl_command)

stdout = send_json_command(repl_command)
print(f"stdout: {stdout}")
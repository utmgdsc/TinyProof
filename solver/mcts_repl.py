import os
import subprocess
import json

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from datasets import load_dataset

device = torch.device("cuda")

model_path = "deepseek-ai/DeepSeek-Prover-V1.5-RL"

# Load tokenizer
quant_tokenizer = AutoTokenizer.from_pretrained(model_path)

# Load models
quant_model = AutoModelForCausalLM.from_pretrained(model_path).to(device)

# Load the validation dataset
dataset = load_dataset("AI-MO/wholeproof-pt-250209-v2", split="train").shuffle(seed=42)

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

# Function to run inference
def generate_response(model, tokenizer, text):
    text = "Complete the following Lean 4 code:\n\nlean```\n" + text
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(**inputs, max_length=4096)
    
    return tokenizer.decode(output[0], skip_special_tokens=True).split("```")[1]

def count_leading_whitespace(s):
    return len(s) - len(s.lstrip())

# TODO :: support adding mutiple goals/errors
def addGoal(ctx, goal):
  # note: line numbers start at 1
  whitespace = 2
  out = ctx + "\n" + whitespace * " " + "/-\n"
  lines = goal.split("\n")
  for line in lines:
    out += (whitespace + 1) * " " + line + "\n"
  out += (whitespace + 1) * " " + "-/"
  return out

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

# prompt = "import Mathlib\n\ntheorem womp (a b c: Nat) : a + b + c = c + (b + a) := by"
thm = """
/--
The sequence of integers $u_n$ is bounded and satisfies
\[
u_n = \frac{u_{n-1} + u_{n-2} + u_{n-3}u_{n-4}}{u_{n-1}u_{n-2} + u_{n-3} + u_{n-4}}.
\]
Show that it is periodic for sufficiently large $n$.
-/
theorem putnam_1964_a4 (u : ℕ → ℤ) (boundedu : ∃ B T : ℤ, ∀ n : ℕ, B ≤ u n ∧ u n ≤ T) (hu : ∀ n ≥ 4, u n = ((u (n - 1) + u (n - 2) + u (n - 3) * u (n - 4)) : ℝ) / (u (n - 1) * u (n - 2) + u (n - 3) + u (n - 4)) ∧ (u (n - 1) * u (n - 2) + u (n - 3) + u (n - 4)) ≠ 0) : (∃ N c : ℕ, c > 0 ∧ ∀ n ≥ N, u (n + c) = u n) := by 
"""
prompt = "import Mathlib\n\n" + thm
proofState = json.loads(send_json_command({ "cmd": prompt + " sorry"}))["sorries"][0]["proofState"]
while True:
  temp = generate_response(quant_model, quant_tokenizer, prompt)[len(prompt):]
  lines = temp.split("\n")

  goals = None

  for index in range(len(lines)):
    repl_command = { "tactic" : "(\n" + "\n".join(lines[:index + 1]) + "\n)", "proofState" : proofState }
    cmd_out = send_json_command(repl_command)
    output = json.loads(cmd_out)
    # print("line: ", lines[:index + 1])
    # print("out: ", output)
    if not "goals" in output:
       continue
    goals = output["goals"]
    break
  
  temp = "\n".join(lines[:index + 1])

  print(prompt)
  print(temp)

  if goals is None:
     continue
  
  if len(goals) == 0:
     break

  prompt = addGoal(prompt + temp, goals[0])

import os
import subprocess
import json

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from datasets import load_dataset

import sys

device = torch.device("cuda")

model_path = "deepseek-ai/DeepSeek-Prover-V1.5-RL"

# Load tokenizer
quant_tokenizer = AutoTokenizer.from_pretrained(model_path)

# Load models
quant_model = AutoModelForCausalLM.from_pretrained(model_path).to(device)

# Load the validation dataset
dataset = load_dataset("AI-MO/wholeproof-pt-250209-v2", split="train").shuffle(seed=42)

# Function to run inference
def generate_response(model, tokenizer, text):
    text = "Complete the following Lean 4 code:\n\n```lean4\n" + text
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(**inputs, max_length=512)

    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)

    try:
        # Find the part after ```lean4\n
        start_marker = "```lean4\n"
        code_start_index = decoded_output.index(start_marker) + len(start_marker)
        # Find the closing ``` after the start marker
        code_end_index = decoded_output.index("```", code_start_index)
        extracted_code = decoded_output[code_start_index:code_end_index].strip() # Use strip()
        return extracted_code
    except ValueError:
        print("Error: Could not extract code block from model output.")
        return ""


def count_leading_whitespace(s):
    return len(s) - len(s.lstrip())

def send_json_command(command):
  """Send JSON command and read response from subprocess."""
  json_input = json.dumps(command, ensure_ascii=False) + "\n\n"
  
  process.stdin.write(json_input)
  process.stdin.flush()  # Ensure input is sent
      
  output_lines = []
  while True:
    line = process.stdout.readline().strip()
    # print("line: ", line)
    if not line:  # Stop reading when there's no more output
        break
    output_lines.append(line)
  return "\n".join(output_lines)

# TODO :: support adding mutiple goals/errors
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

prompt = "import Mathlib\n\ntheorem womp (a b c: Nat) : a + b + c = c + (b + a) := by"


while True:
  temp = generate_response(quant_model, quant_tokenizer, prompt)
  print(temp)
  # Create a proper JSON command for the Lake REPL
  repl_command = { "cmd" : temp, "infotree": "tactics"  }

  stdout = send_json_command(repl_command)
  # print("stdout:", stdout)
  # print("type of dogs:", type(stdout))

  output = json.loads(stdout)


  messages = output.get("messages")
  if messages is None or len(getErrors(messages)) == 0:
    break
  node = getLastTacticNode(output["infotree"][0])
  prompt = addGoal(temp, node['node']['stx']['range']['finish'], node['node']['goalsBefore'][0])
  # print("Stderr:", process.stderr)

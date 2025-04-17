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

# Function to run inference
def generate_response(model, tokenizer, text):
    text = "Complete the following Lean 4 code:\n\n```lean4\n" + text
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(**inputs, max_length=512)
    
    return tokenizer.decode(output[0], skip_special_tokens=True).split("```")[1]

def count_leading_whitespace(s):
    return len(s) - len(s.lstrip())

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

prompt = "import Mathlib\n\ntheorem womp {α : Type} (r s t : Set α) : r ⊆ s → s ⊆ t → r ⊆ t := by"
while True:
  temp = generate_response(quant_model, quant_tokenizer, prompt)
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

  print("stderr:", process.stderr)
  print("stdout:", process.stdout)
  output = json.loads(process.stdout)
  print(output)
  messages = list(filter(lambda x: x["severity"] == "error", output.get("messages")))
  if messages is None or len(getErrors(messages)) == 0:
    break
  node = getLastTacticNode(output["infotree"][0])
  prompt = addGoal(temp, node['node']['stx']['range']['finish'], node['node']['goalsBefore'][0])
  # print("Stderr:", process.stderr)

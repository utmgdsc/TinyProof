import os
import time
import torch
import torch.multiprocessing as mp
from transformers import AutoModelForCausalLM, AutoTokenizer
from prover.utils import AttrDict, MODEL_FORMAT

class GeneratorProcess(mp.Process):
    def __init__(self, local_rank, node_rank, model_path, task_queue, request_statuses, lock, args):
        super().__init__()
        self.local_rank = local_rank
        self.node_rank = node_rank
        self.model_path = model_path
        self.task_queue = task_queue
        self.request_statuses = request_statuses
        self.lock = lock
        self.sampling_params = {
            'temperature': args.temperature,
            'max_length': args.max_tokens,
            'top_p': args.top_p,
        }
        self.prompt_func = MODEL_FORMAT[args.mode]['prompt']
        self.output_func = MODEL_FORMAT[args.mode]['output']
        
    def run(self):
        seed = int(time.time()) % 1000 + (self.node_rank * 8 + self.local_rank) * 1000
        os.environ['LOCAL_RANK'] = str(self.local_rank)
        
        # set random seed for reproducibility
        torch.manual_seed(seed)
        
        # load the model and tokenizer
        device = f"cuda:{self.local_rank}" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {device}")
        
        # tokenizer for transformers model
        tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        
        # configure model loading based on device
        if device.startswith("cuda"):
            model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,  # use half precision for GPU
                trust_remote_code=True,
                device_map=device
            )
        elif device == "mps":
            # try to load to MPS (might run out of space)
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # MPS works better with half precision
                    trust_remote_code=True
                ).to(device)
            except Exception as e:
                print("Loading model to CPU, because model failed to load to MPS:")
                device = "cpu"
        if device == "cpu":
            # CPU fallback
            model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32,  # use full precision for CPU
                trust_remote_code=True
            ).to(device)
        
        # execute tasks
        while True:
            inputs = self.task_queue.get()
            if inputs is None:  # terminate when receiving None
                break
            
            # get model inputs
            model_inputs = [
                ''.join([
                    item.get('_extra_header', str()),
                    self.prompt_func(item),
                    item.get('_extra_prompt', str()),
                ]) for _, _, item in inputs
            ]

            # tokenize inputs (NOTE: vLLM doesn't need this step for unknown reason)
            tokenized_inputs = tokenizer(model_inputs, return_tensors='pt', padding=True, truncation=True)

            # generate results parallel
            model_outputs = model.generate(
                input_ids=tokenized_inputs['input_ids'],
                attention_mask=tokenized_inputs['attention_mask'],
                **self.sampling_params
            )

            outputs = [self.output_func(tokenizer.decode(output, skip_special_tokens=True)) for output in model_outputs]
            with self.lock:
                for (_, request_id, _), output in zip(inputs, outputs):
                    self.request_statuses[request_id] = output
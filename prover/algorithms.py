import os
import json
import time
import numpy as np
from pathlib import Path

class Sampling:
    def __init__(self, scheduler, model, tokenizer, process_print, cfg):
        self.scheduler = scheduler
        self.model = model
        self.tokenizer = tokenizer
        self.process_print = process_print
        self.cfg = cfg
        self.algorithm_name = 'sampling'

    def generate(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.cfg.max_tokens,
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        
        # Get only the newly generated text by finding where the prompt ends
        generated_text = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        return generated_text

    def sample(self, data, prob_log_dir):
        prompt = data['prompt']
        for sample_idx in range(self.cfg.sample_num):
            if sample_idx > 0 and sample_idx % self.cfg.log_interval == 0:
                self.process_print(f'Sampling {sample_idx} / {self.cfg.sample_num}')
            
            # Generate proof attempt
            proof_code = self.generate(prompt)
            
            yield proof_code, {
                'sample_idx': sample_idx,
                'algorithm': self.algorithm_name,
            }


class RMaxTS:
    def __init__(self, scheduler, model, tokenizer, process_print, cfg):
        self.scheduler = scheduler
        self.model = model
        self.tokenizer = tokenizer
        self.process_print = process_print
        self.cfg = cfg
        self.algorithm_name = 'rmaxts'
        
        # RMaxTS specific initialization
        self.gamma = cfg.gamma
        self.concurrent_num = cfg.concurrent_num
        self.tactic_state_comment = cfg.tactic_state_comment
        self.ckpt_interval = cfg.get('ckpt_interval', 128)
        
    def generate(self, prompt, num_samples=1):
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True).to(self.model.device)
        
        # Generate multiple samples at once
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.cfg.max_tokens,
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
            num_return_sequences=num_samples,
        )
        
        # Process all generated sequences
        generated_texts = []
        for output in outputs:
            # Get only the newly generated text
            new_text = self.tokenizer.decode(output[inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            generated_texts.append(new_text)
            
        return generated_texts

    def sample(self, data, prob_log_dir):
        prompt = data['prompt']
        total_samples = 0
        best_reward = -float('inf')
        running_stats = []
        
        while total_samples < self.cfg.sample_num:
            # Generate concurrent_num samples
            batch_size = min(self.concurrent_num, self.cfg.sample_num - total_samples)
            proof_attempts = self.generate(prompt, num_samples=batch_size)
            
            for sample_idx, proof_code in enumerate(proof_attempts):
                total_samples += 1
                
                # Calculate reward (you'll need to implement this based on your specific needs)
                reward = self._calculate_reward(proof_code)
                
                # Update running statistics
                running_stats.append({
                    'reward': reward,
                    'total_samples': total_samples,
                    'best_reward': max(best_reward, reward)
                })
                best_reward = max(best_reward, reward)
                
                # Log progress
                if total_samples % self.cfg.log_interval == 0:
                    self.process_print(f'Sampling {total_samples} / {self.cfg.sample_num} Best reward: {best_reward:.4f}')
                
                # Save checkpoint if needed
                if self.ckpt_interval > 0 and total_samples % self.ckpt_interval == 0:
                    checkpoint_path = os.path.join(prob_log_dir, f'checkpoint_{total_samples}.json')
                    with open(checkpoint_path, 'w') as f:
                        json.dump(running_stats, f)
                
                yield proof_code, {
                    'sample_idx': total_samples - 1,
                    'algorithm': self.algorithm_name,
                    'reward': reward,
                    'best_reward': best_reward
                }

    def _calculate_reward(self, proof_code):
        # Implement reward calculation based on your specific needs
        # This could involve evaluating the proof's correctness, length, or other metrics
        # For now, returning a random reward as placeholder
        return np.random.random()
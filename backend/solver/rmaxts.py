import math
import random
from typing import List, Tuple

import torch
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer

from solver.dummy import NotAVerifier


class Node:
    def __init__(self, state: str, parent=None):
        self.state: str = state
        self.parent = parent
        self.children: List[Tuple[str, float, "Node"]] = []  # (tactic, prior_prob, child_node)
        self.visit_count: int = 0
        self.total_reward: float = 0.0


class RMaxTS:
    """
    RMaxTS proof search integrating DeepSeek model for tactic generation
    and a verifier for proof state validity.
    """
    def __init__(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        verifier=NotAVerifier(),
        num_sequences: int = 5,
        max_new_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.95,
        do_sample: bool = True,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.verifier = verifier
        self.num_sequences = num_sequences
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.do_sample = do_sample
        self.verification_cache = {}

    def verify_state(self, state: str) -> Tuple[bool, bool]:
        """
        Verify a proof state. Returns (is_valid, is_complete).
        Uses a cache to avoid redundant remote calls.
        """
        if state not in self.verification_cache:
            is_valid, is_complete = self.verifier.verify(state)
            self.verification_cache[state] = (is_valid, is_complete)
        return self.verification_cache[state]

    def is_terminal(self, node: Node) -> bool:
        """A node is terminal if invalid or proof complete."""
        is_valid, is_complete = self.verify_state(node.state)
        return (not is_valid) or is_complete

    def is_proof_complete(self, state: str) -> bool:
        """Check if a proof state is complete."""
        _, is_complete = self.verify_state(state)
        return is_complete

    def generate_tactics(self, state: str) -> List[Tuple[str, float]]:
        """
        Use the language model to propose a set of tactics.
        Returns a list of (tactic_str, prior_probability).
        """
        inputs = self.tokenizer(state, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            inputs["input_ids"],
            max_new_tokens=self.max_new_tokens,
            num_return_sequences=self.num_sequences,
            do_sample=self.do_sample,
            temperature=self.temperature,
            top_p=self.top_p,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        tactics = []
        for idx, out in enumerate(outputs):
            # extract generated tokens after the prompt length
            prompt_len = inputs["input_ids"].shape[1]
            tactic = self.tokenizer.decode(out[prompt_len:], skip_special_tokens=True).strip()
            prior = 1.0 / (idx + 1) if not self.do_sample else 1.0 / self.num_sequences
            tactics.append((tactic, prior))
        return tactics

    def select(self, node: Node) -> Node:
        """
        Select a leaf to expand using UCT formula.
        """
        while node.children and not self.is_terminal(node):
            total_N = sum(child_node.visit_count for _, _, child_node in node.children) + 1
            log_total = math.log(total_N)
            best_score = -float("inf")
            best_child = None
            for tactic, prior, child_node in node.children:
                if child_node.visit_count == 0:
                    score = prior
                else:
                    score = (child_node.total_reward / child_node.visit_count) + math.sqrt(
                        2 * log_total / child_node.visit_count
                    )
                if score > best_score:
                    best_score = score
                    best_child = child_node
            node = best_child
        return node

    def expand(self, node: Node) -> Node:
        """
        Expand a leaf by generating child nodes for each tactic.
        """
        for tactic, prob in self.generate_tactics(node.state):
            new_state = node.state + "\n" + tactic
            child = Node(new_state, parent=node)
            node.children.append((tactic, prob, child))
        return node

    def simulate(self, node: Node, max_depth: int = 5) -> float:
        """
        Perform a random rollout from this node to estimate reward.
        """
        state = node.state
        for _ in range(max_depth):
            valid, complete = self.verify_state(state)
            if not valid:
                return 0.0
            if complete:
                return 1.0
            tactics = self.generate_tactics(state)
            if not tactics:
                return 0.0
            # random pick
            state += "\n" + random.choice(tactics)[0]
        return 0.0

    def backup(self, path: List[Node], reward: float):
        """
        Backpropagate reward along the path of nodes.
        """
        for node in path:
            node.visit_count += 1
            node.total_reward += reward

    def search_best_tactic(self, initial_state: str, num_iterations: int = 100) -> str:
        """
        Run MCTS for a fixed number of iterations to choose the next tactic.
        """
        self.root = Node(initial_state)
        valid, _ = self.verify_state(initial_state)
        if not valid:
            return None

        for _ in range(num_iterations):
            leaf = self.select(self.root)
            if self.is_terminal(leaf):
                reward = 1.0 if self.is_proof_complete(leaf.state) else 0.0
            else:
                expanded = self.expand(leaf)
                reward = self.simulate(expanded)
            # collect path
            path = []
            node = leaf
            while node:
                path.append(node)
                node = node.parent
            self.backup(path, reward)

        # choose child with highest visit count
        best = max(self.root.children, key=lambda x: x[2].visit_count)
        return best[0]

    def generate_whole_proof(self, theorem: str, iterations_per_sim: int = 100):
        """
        Iteratively apply search_best_tactic until proof completes or fails.
        Yields each tactic, then the final state.
        """
        state = theorem
        while True:
            valid, complete = self.verify_state(state)
            if not valid:
                break
            if complete:
                break
            tactic = self.search_best_tactic(state, iterations_per_sim)
            if tactic is None:
                break
            yield tactic
            state += "\n" + tactic
        # finally yield the full proof state
        yield state

    def close(self):
        """
        Cleanup verifier resources if applicable.
        """
        if hasattr(self.verifier, "close"):
            self.verifier.close()

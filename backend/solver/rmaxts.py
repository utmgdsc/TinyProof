"""
RMaxTS Proof Search.
"""

# frameworks
import math
import random

class Node:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []  # List of (tactic, prior_prob, child_node)
        self.visit_count = 0
        self.total_reward = 0.0

class RMaxTS:
    def __init__(self, model, tokenizer, verifier, c=1.0, b=1.0, max_depth=10, num_beams=5):
        self.model = model
        self.tokenizer = tokenizer
        self.verifier = verifier
        self.c = c  # Exploration constant for UCT
        self.b = b  # Intrinsic reward bonus for RMaxTS exploration
        self.max_depth = max_depth
        self.num_beams = num_beams
        self.root = None
        self.verification_cache = {}  # Cache: state -> (is_valid, is_complete)

    def verify_state(self, state):
        """Verify a state, using cache to avoid redundant checks."""
        if state not in self.verification_cache:
            # TODO: modify verifier implementation
            is_valid, is_complete = self.verifier.verify(state)
            self.verification_cache[state] = (is_valid, is_complete)
        return self.verification_cache[state]

    def is_terminal(self, node):
        """A node is terminal if invalid or proof is complete."""
        is_valid, is_complete = self.verify_state(node.state)
        return not is_valid or is_complete

    def is_proof_complete(self, state):
        """Check if the proof is complete."""
        _, is_complete = self.verify_state(state)
        return is_complete

    def generate_tactics(self, state, num_beams=None, do_sample=False):
        """
        Generate possible next tactics using the language model.
        """
        if num_beams is None:
            num_beams = self.num_beams
        
        inputs = self.tokenizer(state + "\nNext tactic: ", return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=50,
            num_beams=num_beams,
            num_return_sequences=num_beams if not do_sample else 1,
            do_sample=do_sample,
            temperature=0.7 if do_sample else None,
            pad_token_id=self.tokenizer.eos_token_id
        )
        tactics = []
        for i, output in enumerate(outputs):
            tactic = self.tokenizer.decode(output[inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            prior_prob = 1.0 / (i + 1) if not do_sample else 0.5
            tactics.append((tactic, prior_prob))
        return tactics

    def select(self, node):
        """
        Select a node to expand using UCT with RMaxTS bonus.
        """
        while node.children and not self.is_terminal(node):
            node = max(
                node.children,
                key=lambda x: self.uct_value(x[2], node.visit_count),
                default=None
            )[2]
        return node

    def uct_value(self, child_node, parent_visits):
        """
        Compute UCT value with intrinsic exploration bonus.
        """
        if child_node.visit_count == 0:
            return float("inf")
        exploitation = child_node.total_reward / child_node.visit_count
        exploration = self.c * math.sqrt(math.log(parent_visits) / child_node.visit_count)
        bonus = self.b / math.sqrt(child_node.visit_count)  # RMaxTS intrinsic reward
        return exploitation + exploration + bonus

    def expand(self, node):
        """
        Expand node by generating valid child states.
        """
        tactics = self.generate_tactics(node.state)
        for tactic, prior_prob in tactics:
            new_state = node.state + "\n" + tactic
            is_valid, is_complete = self.verify_state(new_state)
            if is_valid:  # Only add valid states, truncating invalid paths
                child_node = Node(new_state, parent=node)
                node.children.append((tactic, prior_prob, child_node))

    def simulate(self, state):
        """
        Simulate a random proof path until terminal or max depth.
        """
        current_state = state
        depth = 0
        while depth < self.max_depth:
            is_valid, is_complete = self.verify_state(current_state)
            if not is_valid:  # Truncate on error
                return 0.0
            if is_complete:  # Success
                return 1.0
            tactics = self.generate_tactics(current_state, num_beams=1, do_sample=True)
            if not tactics:
                break
            tactic, _ = tactics[0]
            current_state += "\n" + tactic
            depth += 1
        # Check final state after max_depth
        _, is_complete = self.verify_state(current_state)
        return 1.0 if is_complete else 0.0

    def backpropagate(self, node, reward):
        """
        Update node statistics up the tree.
        """
        while node is not None:
            node.visit_count += 1
            node.total_reward += reward
            node = node.parent

    def search_best_tactic(self, initial_state, num_iterations=100):
        """
        Perform RMaxTS search to find the best next tactic.
        """
        self.root = Node(initial_state)
        is_valid, _ = self.verify_state(initial_state)
        if not is_valid:
            return None  # Invalid initial state

        for _ in range(num_iterations):
            node = self.select(self.root)
            if self.is_terminal(node):
                reward = 1.0 if self.is_proof_complete(node.state) else 0.0
            else:
                self.expand(node)
                if node.children:
                    child = random.choice(node.children)[2]
                    reward = self.simulate(child.state)
                else:
                    reward = 0.0  # No valid children
            self.backpropagate(node, reward)

        # Select the best child tactic based on visit count
        if not self.root.children:
            return None
        best_child = max(self.root.children, key=lambda x: x[2].visit_count)
        return best_child[0]  # Return the tactic
    
    def generate_whole_proof(self, theorem: str, iterations_per_sim: int = 100):
        """
        Run a proof search given a theorem prompt.

        params
        theorem: the initial theorem statement
        iterations_per_sim: number of iterations per MCTS simulation for next tactic
        """
        current_state = theorem
        proof_steps = []

        while True:
            is_valid, is_complete = self.verify_state(current_state)
            if not is_valid:
                print("Invalid state reached. Stopping.")
                break
            if is_complete:
                print("Proof complete!")
                break
            best_tactic = self.search_best_tactic(current_state, num_iterations = iterations_per_sim)

            # happens e.g. if input theorem is invalid, no valid child states generated, exhausted search space
            if best_tactic is None:
                print("No valid tactics found. Stopping.")
                break
            print("Applying tactic:", best_tactic)
            proof_steps.append(best_tactic)
            current_state += "\n" + best_tactic

        print("Final proof state:", current_state)
        print("Proof steps:", proof_steps)

        #return proof_steps


if __name__ == "__main__":
    pass
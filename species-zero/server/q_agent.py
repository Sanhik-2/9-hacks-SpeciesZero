import random
import difflib
from persistence import save_state, load_state

class QAILogic:
    def __init__(self, action_size=7, model_path="q_table.npz"):
        self.action_size = action_size
        self.model_path = model_path
        
        # Load state
        q_table, adapted, registry, wins = load_state(self.model_path)
        self.q_table = q_table  # dict: str(state) -> list of state-action values
        self.adapted_phenomena = adapted  # set of strings
        self.adaptation_registry = registry  # dict: phenomenon_id -> hit count
        self.consecutive_wins = wins
            
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.1
        
    def _get_q_values(self, state):
        state_key = str(state)
        if state_key not in self.q_table:
            # Initialize newly encountered state with zeros
            self.q_table[state_key] = [0.0] * self.action_size
        return self.q_table[state_key]

    def get_action(self, state):
        # Epsilon-greedy exploration
        if random.uniform(0, 1) < self.epsilon:
            return random.randint(0, self.action_size - 1)
            
        q_values = self._get_q_values(state)
        # return action with highest Q-value
        return q_values.index(max(q_values))
        
    def update(self, state, action, reward, next_state):
        state_key = str(state)
        
        current_q = self._get_q_values(state)[action]
        best_next_q = max(self._get_q_values(next_state))
        
        td_target = reward + self.discount_factor * best_next_q
        td_error = td_target - current_q
        
        self.q_table[state_key][action] += self.learning_rate * td_error
        
        # Persistence
        save_state(self.q_table, self.adapted_phenomena, self.adaptation_registry, self.consecutive_wins, self.model_path)

    def check_semantic_similarity(self, phenomenon_id):
        """Returns True if there is a similar phenomenon already adapted to (>60% match)."""
        for adapted in self.adapted_phenomena:
            similarity = difflib.SequenceMatcher(None, phenomenon_id, adapted).ratio()
            if similarity > 0.6: 
                return True
        return False
        
    def is_adapted(self, phenomenon_id):
        """Returns True if the exact phenomenon is completely adapted."""
        return phenomenon_id in self.adapted_phenomena

    def observe_phenomenon(self, phenomenon_id, increment=1.0):
        """
        Increments adaptation registry passively via Observation Learning.
        Returns True if wheel spin occurs.
        """
        if phenomenon_id == "unknown" or phenomenon_id in self.adapted_phenomena:
            return False
            
        if phenomenon_id not in self.adaptation_registry:
            self.adaptation_registry[phenomenon_id] = 0.0
            
        self.adaptation_registry[phenomenon_id] += increment
        
        if self.adaptation_registry[phenomenon_id] >= 5.0:
            self.adapted_phenomena.add(phenomenon_id)
            save_state(self.q_table, self.adapted_phenomena, self.adaptation_registry, self.consecutive_wins, self.model_path)
            return True
            
        save_state(self.q_table, self.adapted_phenomena, self.adaptation_registry, self.consecutive_wins, self.model_path)
        return False

    def process_adaptation(self, action, current_phenomenon, previous_phenomenon):
        """
        Increments adaptation counters if the AI actively chose to adapt (Action 5 or 6).
        Returns True if a 'Wheel Spin' (full immunity threshold) is reached.
        """
        target_phenomenon = None
        if action == 5 and current_phenomenon:
            target_phenomenon = current_phenomenon
        elif action == 6 and previous_phenomenon:
            target_phenomenon = previous_phenomenon
            
        if not target_phenomenon or target_phenomenon in self.adapted_phenomena:
            return False
            
        if target_phenomenon not in self.adaptation_registry:
            self.adaptation_registry[target_phenomenon] = 0
            
        self.adaptation_registry[target_phenomenon] += 1
        
        # Hit limit logic (5 hits to fully adapt)
        if self.adaptation_registry[target_phenomenon] >= 5:
            self.adapted_phenomena.add(target_phenomenon)
            save_state(self.q_table, self.adapted_phenomena, self.adaptation_registry, self.consecutive_wins, self.model_path)
            return True
            
        save_state(self.q_table, self.adapted_phenomena, self.adaptation_registry, self.consecutive_wins, self.model_path)
        return False

    def process_damage(self, phenomenon_id, base_damage):
        """
        Calculates progressive effective damage taken considering partial and semantic immunities.
        Returns:
            effective_damage (float): The final damage scaled by (1.0 - hits/5.0).
        """
        if phenomenon_id in self.adapted_phenomena:
            return 0.0 # Complete Immunity
            
        effective_damage = float(base_damage)
        
        # Progressive damage reduction
        hits = self.adaptation_registry.get(phenomenon_id, 0)
        fractional_reduction = min(hits, 5) / 5.0
        effective_damage = effective_damage * (1.0 - fractional_reduction)
            
        # Semantic Adaptation check (Further 50% reduction if unadapted but semantically similar)
        if effective_damage > 0 and hits == 0 and self.check_semantic_similarity(phenomenon_id):
            effective_damage *= 0.5 
                
        return effective_damage

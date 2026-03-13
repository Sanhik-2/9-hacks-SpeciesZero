import random
import difflib
import atexit
from persistence import save_state, load_state

class QAILogic:
    def __init__(self, action_size=9, model_path="species_zero_brain.json", mode="training"):
        self.action_size = action_size
        self.model_path = model_path
        self.mode = mode
        
        # Load state
        q_table, adapted, registry, wins, global_timer = load_state(self.model_path)
        self.q_table = q_table  # dict: str(state) -> list of state-action values
        self.adapted_phenomena = adapted  # set of strings
        self.adaptation_registry = registry  # dict: phenomenon_id -> hit count
        self.consecutive_wins = wins
        self.global_combat_timer = global_timer
        self.phenomenon_stats = {} # Track player phenomena counts for Mirror Engine
            
        self.learning_rate = 0.1 if mode == "training" else 0.02
        self.discount_factor = 0.9
        self.epsilon = max(0.05, 0.1 - (self.global_combat_timer / 1000.0) * 0.05) if mode == "training" else 0.05
        self.is_phase_2 = False
        self.consecutive_idles_close = 0
        self.consecutive_idles_far = 0
        self.dopamine_level = 1.0
        
        atexit.register(self.save)
        
    def update_idles(self, action, distance):
        if action == 0 and distance <= 1.5:
            self.consecutive_idles_close += 1
        else:
            self.consecutive_idles_close = 0
            
        if action == 0 and distance > 1.5:
            self.consecutive_idles_far += 1
        else:
            self.consecutive_idles_far = 0
            
    def update_dopamine(self, damage_to_player, user_hp):
        if user_hp < 30.0:
            self.dopamine_level = 2.5 # Lethality Hook
        else:
            if damage_to_player > 0:
                self.dopamine_level = min(5.0, self.dopamine_level + 1.0)
            else:
                self.dopamine_level = max(0.0, self.dopamine_level - 0.1)
        return self.dopamine_level
        
    def _get_q_values(self, state):
        state_key = str(state)
        if state_key not in self.q_table:
            # Aggressive bias: seed new states with a Bloodlust policy
            # Action 0 (Idle) starts negative so the AI never defaults to standing still
            init = [0.0] * self.action_size
            init[0] = -1.0   # Idle: punished from birth
            init[1] =  0.3   # Advance: always a decent option
            init[2] =  0.1   # Dodge/Lateral
            init[3] =  0.5   # Melee Strike: high priority
            init[4] =  0.1   # Block
            init[5] =  0.1   # Adapt
            init[6] =  0.1   # Mimic
            init[7] =  0.6   # Shadow Blitz: highest priority
            init[8] =  0.2   # Evasive Skirmish
            self.q_table[state_key] = init
        return self.q_table[state_key]

    def get_action(self, state, distance=10.0, is_adapted=False, ai_hp=100.0):
        # === BLOODLUST MECHANISM ===
        # The AI must ALWAYS be moving or attacking. Never stand still.
        # Distance-aware aggression:
        if distance > 6.0:
            # TOO FAR: Sprint toward the player. Advance is the only valid option.
            if random.random() < 0.7:
                return 1  # Advance
        elif distance > 2.0:
            # MID RANGE: Blitz territory. Mix Advance and Shadow Lunge.
            if random.random() < 0.5:
                return random.choice([1, 7, 7, 3])  # Blitz-heavy
        else:
            # CLOSE RANGE: Strike zone. Go for the kill.
            if random.random() < 0.5:
                return random.choice([3, 3, 7, 8])  # Melee-heavy
        
        # Desperation override
        if self.dopamine_level < 0.2 and ai_hp < 20.0:
            self.epsilon = 0.0
            if distance > 2.0:
                return 7
                
        # Action 0 (Menacing Idle): If AI is Adapted, distance < 2.0, and idled for 3 turns, force strike/lunge
        if is_adapted and distance < 2.0 and self.consecutive_idles_close >= 3:
            return random.choice([3, 7]) # Force strike or lunge
            
        # The 'Boredom' Gate (Anti-Passivity for Phase 2)
        if self.is_phase_2 and distance > 1.5 and self.consecutive_idles_far > 2:
            return random.choice([1, 7])
            
        # The 'Boredom' Gate (Active Combat)
        if distance <= 1.5 and self.consecutive_idles_close > 2:
            return random.choice([a for a in range(self.action_size) if a != 0])
            
        # Neural Dopamine Override
        if self.dopamine_level > 2.0:
            # Force offensive or evasive actions, block idle
            choices = [a for a in range(self.action_size) if a != 0]
            if random.uniform(0, 1) < self.epsilon:
                return random.choice(choices)
            # Find best non-idle move
            q_values = self._get_q_values(state)[:]
            q_values[0] = -999999.0 # Explicitly block Action 0
            # Apply same aggression/critical boosts if phase 2 or critical
            is_critical = "_Critical_" in str(state) or self.is_phase_2
            if is_critical:
                q_values[3] *= 3.0
                q_values[7] *= 3.0
            if "Far" in str(state):
                q_values[0] -= 1.0
            if "Lunge_Ready" in str(state):
                q_values[7] += 0.5
            return q_values.index(max(q_values))
            
        # Epsilon-greedy exploration
        current_epsilon = 0.01 if self.is_phase_2 else self.epsilon
        if random.uniform(0, 1) < current_epsilon:
            return random.randint(0, self.action_size - 1)
            
        q_values = self._get_q_values(state)[:] # Copy to avoid mutating Q-table
        
        # Aggression Scaling (The "Finish Him" Logic)
        is_critical = "_Critical_" in str(state) or self.is_phase_2
        if is_critical:
            # Weights Action 3 (Melee) and Action 7 (Blitz) by 3.0x
            q_values[3] *= 3.0
            q_values[7] *= 3.0
            
            # Action 0 logic: Drop Idle chance to 0% (Fatal Decision)
            q_values[0] = -999999.0 # Effectively removal
            
        # Far Range Idle Penalty
        if "Far" in str(state):
            q_values[0] -= 1.0
            
        # Blitz Prioritization
        if "Lunge_Ready" in str(state):
            q_values[7] += 0.5
            
        # Action with highest Q-value
        # If max value is -999999.0 somehow (shouldn't happen with actions 3/7 weighted), 
        # it will still pick one of the hitters.
        return q_values.index(max(q_values))
        
    def update(self, state, action, reward, next_state, turn=1):
        state_key = str(state)
        
        current_q = self._get_q_values(state)[action]
        best_next_q = max(self._get_q_values(next_state))
        
        td_target = reward + self.discount_factor * best_next_q
        td_error = td_target - current_q
        
        self.q_table[state_key][action] += self.learning_rate * td_error
        
        # Priority Experience Buffer: Explicitly boost actions leading to Victory
        if reward >= 10.0:
            self.q_table[state_key][action] += 5.0 # Massive permanent boost
        
        # Update global combat timer
        self.global_combat_timer += 1
        
        # Save every 50 turns
        if turn % 50 == 0:
            self.save()
            
    def save(self):
        save_state(self.q_table, self.adapted_phenomena, self.adaptation_registry, self.consecutive_wins, self.global_combat_timer, self.model_path)

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
        if phenomenon_id == "unknown":
            return False
            
        # Track stats for Mirror Engine
        if phenomenon_id != "none":
            self.phenomenon_stats[phenomenon_id] = self.phenomenon_stats.get(phenomenon_id, 0) + 1

        if phenomenon_id in self.adapted_phenomena:
            return False
            
        if phenomenon_id not in self.adaptation_registry:
            self.adaptation_registry[phenomenon_id] = 0.0
            
        self.adaptation_registry[phenomenon_id] += increment
        
        if self.adaptation_registry[phenomenon_id] >= 5.0:
            self.adapted_phenomena.add(phenomenon_id)
            self.save()
            return True
            
        self.save()
        return False

    def get_mirror_target(self):
        """Returns the most used phenomenon_id for Action 6 Mimicry."""
        if not self.phenomenon_stats:
            return None
        return max(self.phenomenon_stats, key=self.phenomenon_stats.get)

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
            self.save()
            return True
            
        self.save()
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

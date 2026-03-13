def calculate_reward(damage_to_player, effective_damage_taken, turn, action, ai_hp, user_hp, distance, is_adapted_to_ranged=False, is_player_dead=False):
    """
    Calculate the reward scaled between -1.0 and +1.0 to transition the AI into a Tactical Hunter.
    """
    reward = 0.0
    
    # Tactical action preferences
    if action == 2: # Dodge (Slight positive reinforcing of evasion)
        reward += 0.1
    elif action == 3 and damage_to_player > 0: # Successful Melee Strike
        reward += 0.3
        reward += 0.05 # Efficiency Bonus
    elif action == 4 and damage_to_player > 0: # Successful Ranged
        reward += 0.1
        reward += 0.05 # Efficiency Bonus
    elif action == 7 and damage_to_player > 0: # Successful Blitz Assault
        reward += 0.4
    elif action in [5, 6]: # Active Adaptation choice
        reward += 0.1

    # Dodge-to-Advance: Reward for moving closer when adapted to ranged projectile
    if action == 1 and is_adapted_to_ranged:
        reward += 0.1
        
    # Vampire Reward
    if damage_to_player > 0:
        reward += (damage_to_player / 100.0) * 2.0

    # Whiff Penalty: Melee at long range
    if action == 3 and distance > 1.5:
        if distance <= 2.0:
            reward -= 1.0  # Double penalty for Close range miss
        else:
            reward -= 0.5
        
    # Vulnerability Penalty: -0.8 per 10 damage taken (Overpowers standard attack joy)
    if effective_damage_taken > 0:
        reward -= (effective_damage_taken / 10.0) * 0.8
        
    # The Executioner Time Penalty (Compounding Decay)
    penalty = (1.15 ** turn) / 100.0
    if action == 7:
        penalty *= 2.0  # 2.0x Stamina cost for Blitzing
    reward -= penalty
        
    # Desperation logic if near death
    if ai_hp <= 15 and action == 2:
        reward += 0.2
        
    # Cap normal game loop events
    reward = max(-1.0, min(1.0, float(reward)))
        
    # Absolute overrides: Termination conditions
    if ai_hp <= 0:
        return -1.0
    elif user_hp <= 0 or is_player_dead:
        return 5.0
        
    return reward

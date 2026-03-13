def calculate_reward(damage_to_player, effective_damage_taken, turn, action, ai_hp, user_hp, is_player_dead=False):
    """
    Calculate the reward scaled between -1.0 and +1.0 to transition the AI into a Tactical Hunter.
    """
    reward = 0.0
    
    # Tactical action preferences
    if action == 2: # Dodge (Slight positive reinforcing of evasion)
        reward += 0.1
    elif action == 3 and damage_to_player > 0: # Successful Strike
        reward += 0.3
    elif action in [4, 5]: # Active Adaptation choice
        reward += 0.1
        
    # Vulnerability Penalty: -0.8 per 10 damage taken (Overpowers standard attack joy)
    if effective_damage_taken > 0:
        reward -= (effective_damage_taken / 10.0) * 0.8
        
    # Desperation logic if near death
    if ai_hp <= 15 and action == 2:
        reward += 0.2
        
    # Cap normal game loop events
    reward = max(-1.0, min(1.0, float(reward)))
        
    # Absolute overrides: Termination conditions
    if ai_hp <= 0:
        return -1.0
    elif user_hp <= 0 or is_player_dead:
        return 1.0
        
    return reward

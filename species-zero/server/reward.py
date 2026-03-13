def calculate_reward(damage_to_player, effective_damage_taken, turn, action, ai_hp, user_hp, is_player_dead=False):
    """
    Calculate the reward based on aggressive hunter philosophy, time limits, and survival instinct.
    """
    if turn <= 5:
        reward = -1.0 # Early turn penalty
    elif turn <= 10:
        reward = -5.0 # Mid game penalty
    else:
        reward = -20.0 # Late game desperate penalty
        
    # Standard Damage logic 
    damage_penalty = (float(effective_damage_taken) * 15.0)
    
    # Low Health Multiplier (Fear of Death)
    if ai_hp < 30:
        damage_penalty *= 2.0
        
    reward -= damage_penalty
    reward += (float(damage_to_player) * 10.0)        # Fixed scale for landing hits
    
    # Desperation Incentive: Reward Dodging if critically low.
    if ai_hp < 15 and action == 2:
        reward += 2.0
        
    # Active Adaptation Incentive: Reward adapting behavior
    if action in [4, 5]:
        reward += 5.0
        
    # Termination conditions
    if ai_hp <= 0:
        reward -= 500.0
        
    if user_hp <= 0 or is_player_dead:
        reward += 200.0
        
    return reward

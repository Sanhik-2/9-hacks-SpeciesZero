def calculate_reward(damage_to_player, effective_damage_taken, turn, action, ai_hp, user_hp, distance, is_adapted_to_current=False, is_player_dead=False, consecutive_idles=0, phenomenon_id="none", dopamine_level=1.0, is_phase_2=False):
    """
    Calculate the reward scaled between -1.0 and +1.0 to transition the AI into a Tactical Hunter.
    incorporating specific phenomenon_id priorities (attack, block, ambush, counterattack).
    """
    reward = 0.0
    
    # 3D Spatial Correction
    if distance <= 0.0 and action == 1:
        reward -= 1.0

    # Aggression Bias (Hunger Mechanic)
    if user_hp <= 70.0 and action in [3, 7]:
        reward += 0.2
        
    # Terminal Goal: Aggression +0.2 for distance reduced or damage dealt
    if action in [1, 7] or damage_to_player > 0:
        reward += 0.2
        
    # 2. DOPAMINE FLOW: Motivation Engine
    if damage_to_player > 0:
        reward += (damage_to_player * 0.1) * dopamine_level

    # The Boredom Penalty
    if action == 0 and distance <= 1.5 and consecutive_idles > 2:
        reward -= 0.1 * (consecutive_idles - 2)
        
    # 3. ANTI-STAGNATION: Cowardice Penalty
    if action == 0 and distance < 6.0:
        reward -= 0.5 * (1.0 / (dopamine_level + 0.1))

    
    # Tactical action preferences
    if action == 2: # Dodge (Slight positive reinforcing of evasion)
        reward += 0.1
    elif action == 3 and damage_to_player > 0: # Successful Melee Strike
        reward += 0.3 * dopamine_level
        reward += 0.05 # Efficiency Bonus
    elif action == 4 and damage_to_player > 0: # Successful Ranged
        reward += 0.1
        reward += 0.05 # Efficiency Bonus
    elif action == 7: # Blitz Assault
        if damage_to_player > 0:
            reward += 0.4 * dopamine_level
        if 3.0 <= distance <= 6.0:  # The "Shadow Lunge" optimal range
            reward += 1.0 * dopamine_level  # Heavily rewarded
    elif action in [5, 6]: # Active Adaptation choice
        reward += 0.1

    # Strategic Combat Re-mapping Adaptive Weights
    if phenomenon_id == "block" and action == 6:
        # Mockery/Mimicry bypasses shields
        reward += 0.6
    elif phenomenon_id == "ambush" and action == 2:
        # Lateral dodge escapes ambush
        reward += 0.4
    elif phenomenon_id == "counterattack" and action == 0:
        # Idle baits cooldown
        reward += 0.4

    # Dodge-to-Advance: Reward for moving closer when adapted to ranged projectile
    if action == 1 and is_adapted_to_current:
        reward += 0.1
        
    # Proximity Incentive: Stalking Reward
    if action in [1, 7]:
        reward += 0.1

    # Vampire Reward
    if damage_to_player > 0:
        reward += (damage_to_player / 100.0) * 2.0

    # Whiff Penalty: Melee at long range
    if action == 3 and distance > 1.5:
        if distance <= 2.0:
            reward -= 2.0  # Double penalty for Close range miss
        else:
            reward -= 1.0
            
    # Relentless: Stagnation Penalty for Idling while immune
    if action == 0 and is_adapted_to_current: # Simplified check for 'adapted to current'
        reward -= 2.0
        
    # Vulnerability Penalty: -0.8 per 10 damage taken (Overpowers standard attack joy)
    if effective_damage_taken > 0:
        reward -= (effective_damage_taken / 10.0) * 0.8
        
    # The Executioner Time Penalty (Compounding Decay)
    penalty = (1.15 ** turn) / 100.0
    if action == 7:
        penalty *= 2.0  # 2.0x Stamina cost for Blitzing
    penalty = min(penalty, 0.5)
    reward -= penalty
        
    # Desperation logic if near death
    if ai_hp <= 15 and action == 2:
        reward += 0.2
        
    # Lethality Bonus
    if user_hp <= 30.0:  # Critical Bucket
        reward += 0.5
        
    # 4. PHASE 2 AGGRESSION
    if is_phase_2:
        reward *= 1.5
        
    # Cap normal game loop events
    reward = max(-1.0, min(1.0, float(reward)))
        
    # Absolute overrides: Termination conditions
    if ai_hp <= 0:
        return -1.0
    elif user_hp <= 0 or is_player_dead:
        return 20.0  # The ultimate Dopamine spike
        
    return reward

from flask import Flask, request, jsonify
import os
from q_agent import QAILogic
from validate_telemetry import validate_act_state, validate_update_state
from reward import calculate_reward

app = Flask(__name__)
# Actions: 0: Idle, 1: Advance, 2: Dodge, 3: Melee, 4: Ranged, 5: Adapt Current, 6: Adapt Previous, 7: Blitz Assault, 8: Evasive Skirmish
mode = os.environ.get("AGENT_MODE", "training")
agent = QAILogic(action_size=9, model_path="species_zero_brain.json", mode=mode)

@app.route("/act", methods=["POST"])
def act():
    data = request.json
    # 3D State Vector: x, y, z relative positions, velocity, etc.
    rel_pos = data.get("relative_position", [0, 0, 0]) # [x, y, z]
    vertical_level = data.get("vertical_level", "Grounded") # Grounded, Airborne
    velocity_type = data.get("velocity", "Stationary") # Stationary, Moving
    
    # 3D Discretized State Conversion
    # Relative_Position: (Front, Back, Left, Right)
    x, y, z = rel_pos
    distance = float(data.get("distance", 10.0))
    pos_desc = "Front"
    if distance > 6.0:
        pos_desc = "Far"
    elif z < -1: pos_desc = "Back"
    elif x > 1: pos_desc = "Right"
    elif x < -1: pos_desc = "Left"
    
    state_str = f"{pos_desc}_{vertical_level}_{velocity_type}"
    
    # Check for critical state (inherited from previous logic)
    user_hp = float(data.get("user_hp", 100.0))
    if user_hp < 30:
        state_str += "_Critical_"
        
    # Check for lunge ready
    lunge_range = data.get("lunge_range", "No_Lunge")
    if lunge_range == "Lunge_Ready":
        state_str += "_Lunge_Ready_"

    # Assuming current phenomenon is unknown for act (since player might not have attacked yet), but we can pass False or current checking 
    phenomenon_id = data.get("phenomenon_id", "none")
    is_adapted = agent.is_adapted(phenomenon_id)
    ai_hp = float(data.get("ai_hp", 100.0))

    action = agent.get_action(state_str, distance, is_adapted, ai_hp)
    
    return jsonify({
        "action": int(action),
        "discretized_state": state_str
    })

@app.route("/update", methods=["POST"])
def update():
    data = request.json
    valid, err = validate_update_state(data)
    if not valid:
        return jsonify({"error": err}), 400
        
    state = data.get("state") # Current state string or reconstructed
    action = int(data.get("action", 0))
    next_state = data.get("next_state")
    phenomenon_id = data.get("phenomenon_id", "unknown")
    previous_phenomenon_id = data.get("previous_phenomenon_id", None)
    damage_taken = float(data.get("damage_taken", 0.0))
    damage_to_player = float(data.get("damage_to_player", 0.0))
    user_hp = float(data.get("user_hp", 100.0))
    ai_hp = float(data.get("ai_hp", 100.0))
    distance = float(data.get("distance", 10.0))
    is_player_dead = bool(data.get("is_player_dead", False))
    turn = int(data.get("turn", 1))
    rebirth_trigger = bool(data.get("rebirth_trigger", False))
    
    if rebirth_trigger:
        # Reset turn pressure or any relevant counters for Phase 2
        agent.is_phase_2 = True
    
    agent.update_idles(action, distance)
    dopamine_level = agent.update_dopamine(damage_to_player, user_hp)
    
    # Process incoming damage reductions
    effective_damage = agent.process_damage(phenomenon_id, damage_taken)
    
    # Observation Learning
    spin_from_observation = False
    if action == 2:
        spin_from_observation = agent.observe_phenomenon(phenomenon_id, increment=0.5)
    elif damage_taken > 0:
        spin_from_observation = agent.observe_phenomenon(phenomenon_id, increment=1.0)
    
    # Check if the AI actively chose to adapt this turn
    wheel_spin = agent.process_adaptation(action, phenomenon_id, previous_phenomenon_id)
    
    wheel_spin = wheel_spin or spin_from_observation
    
    # Lethality & Reciprocity Tracking
    if is_player_dead or user_hp <= 0:
        agent.consecutive_wins += 1
        agent.save()  # Persistence: Save when player dies
    if (ai_hp - effective_damage) <= 0:
        agent.consecutive_wins = 0
        
    infused_multiplier = 1.2 if agent.consecutive_wins >= 3 else 1.0
    
    is_adapted_to_current = agent.is_adapted(phenomenon_id)
    
    # Mirror Engine Mockery (only if adapted to current)
    mockery_target = agent.get_mirror_target()
    mockery_flag = (action == 6 and mockery_target is not None and is_adapted_to_current)
    
    if mockery_flag:
        agent.save()  # Mark major learning milestone
    
    # Adaptive Counter flag check (for client visuals/logs if needed)
    is_infused_counter = (action == 3 and is_adapted_to_current)
    
    # Calculate aggressive hunter reward
    reward = calculate_reward(damage_to_player, effective_damage, turn, action, ai_hp, user_hp, distance, is_adapted_to_current, is_player_dead, agent.consecutive_idles_close, phenomenon_id, dopamine_level, agent.is_phase_2)
    
    # Q-Learning update
    agent.update(state, action, reward, next_state, turn)
    
    return jsonify({
        "status": "success",
        "reward_applied": float(reward),
        "effective_damage": float(effective_damage),
        "wheel_spin": wheel_spin,
        "is_infused_counter": is_infused_counter,
        "infused_multiplier": infused_multiplier,
        "mockery_flag": mockery_flag,
        "mockery_target": mockery_target,
        "identity_suppressed": mockery_flag, # Action 6 triggers suppression
        "adapted": list(agent.adapted_phenomena),
        "dopamine_level": float(dopamine_level)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

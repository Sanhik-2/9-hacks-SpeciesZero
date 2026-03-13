from flask import Flask, request, jsonify
from q_agent import QAILogic
from validate_telemetry import validate_act_state, validate_update_state
from reward import calculate_reward

app = Flask(__name__)
# Actions: 0: Idle, 1: Chase, 2: Dodge, 3: Attack, 4: Adapt Current, 5: Adapt Previous
agent = QAILogic(action_size=6, model_path="q_table.npz")

@app.route("/act", methods=["POST"])
def act():
    data = request.json
    valid, err = validate_act_state(data)
    if not valid:
        return jsonify({"error": err}), 400
        
    state = data.get("state")
    action = agent.get_action(state)
    
    return jsonify({"action": int(action)})

@app.route("/update", methods=["POST"])
def update():
    data = request.json
    valid, err = validate_update_state(data)
    if not valid:
        return jsonify({"error": err}), 400
        
    state = data.get("state")
    action = int(data.get("action", 0))
    next_state = data.get("next_state")
    phenomenon_id = data.get("phenomenon_id", "unknown")
    previous_phenomenon_id = data.get("previous_phenomenon_id", None)
    damage_taken = float(data.get("damage_taken", 0.0))
    damage_to_player = float(data.get("damage_to_player", 0.0))
    user_hp = float(data.get("user_hp", 100.0))
    ai_hp = float(data.get("ai_hp", 100.0))
    is_player_dead = bool(data.get("is_player_dead", False))
    turn = int(data.get("turn", 1))
    
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
    
    # Adaptive Counter flag check (for client visuals/logs if needed)
    is_infused_counter = (action == 3 and agent.is_adapted(phenomenon_id))
    
    # Calculate aggressive hunter reward
    reward = calculate_reward(damage_to_player, effective_damage, turn, action, ai_hp, user_hp, is_player_dead)
    
    # Q-Learning update
    agent.update(state, action, reward, next_state)
    
    return jsonify({
        "status": "success",
        "reward_applied": float(reward),
        "effective_damage": float(effective_damage),
        "wheel_spin": wheel_spin,
        "is_infused_counter": is_infused_counter,
        "adapted": list(agent.adapted_phenomena)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

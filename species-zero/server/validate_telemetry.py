def validate_act_state(data):
    """Validate JSON payload for /act endpoint."""
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"
    required = ["phenomenon_id", "state", "distance", "user_action", "incoming_type", "turn_pressure", "user_hp_bucket", "lunge_range"]
    for req in required:
        if req not in data:
            return False, f"Missing required field: {req}"
    return True, None

def validate_update_state(data):
    """Validate JSON payload for /update endpoint."""
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"
    required = ["phenomenon_id", "previous_phenomenon_id", "damage_taken", "damage_to_player", "user_hp", "ai_hp", "is_player_dead", "state", "action", "next_state", "distance", "user_action", "incoming_type", "turn_pressure", "user_hp_bucket", "lunge_range"]
    for req in required:
        if req not in data:
            return False, f"Missing required field: {req}"
    return True, None

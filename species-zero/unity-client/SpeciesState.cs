using System;
using UnityEngine;

[Serializable]
public class SpeciesState
{
    public string state;
    public int action;
    public string next_state;
    public string phenomenon_id;
    public string previous_phenomenon_id;
    public float damage_taken;
    public float damage_to_player;
    public float ai_hp;
    public float user_hp;
    public bool is_player_dead;
    public int turn;
    public bool rebirth_trigger;

    // 3D Specific
    public float[] relative_position; // [x, y, z]
    public string vertical_level; // Grounded, Airborne
    public string velocity; // Stationary, Moving
    public float distance;
    public float target_angle;
}

[Serializable]
public class ActResponse
{
    public int action;
    public string discretized_state;
    public string error;
}

[Serializable]
public class UpdateResponse
{
    public string status;
    public float reward_applied;
    public float effective_damage;
    public bool wheel_spin;
    public bool is_infused_counter;
    public float infused_multiplier;
    public bool mockery_flag;
    public string mockery_target;
    public bool identity_suppressed;
    public string[] adapted;
}

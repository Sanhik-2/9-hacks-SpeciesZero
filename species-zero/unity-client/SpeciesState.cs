using System;

[Serializable]
public class SpeciesState
{
    public string state;
    public string phenomenon_id;
    public string previous_phenomenon_id;
    public float damage_taken;
    public float damage_to_player;
    public float ai_hp;
    public float user_hp;
    public bool is_player_dead;
    public int action;
    public string next_state;
}

[Serializable]
public class ActResponse
{
    public int action;
    public string error;
}

[Serializable]
public class UpdateResponse
{
    public string status;
    public float reward_applied;
    public float effective_damage;
    public bool wheel_spin;
    public string[] adapted;
    public string error;
}

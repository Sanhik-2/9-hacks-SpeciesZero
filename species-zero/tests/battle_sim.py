import requests
import json
import os
import random

SERVER_URL = "http://localhost:5000"

def play_game():
    print("========================================")
    print("      SPECIES ZERO - BATTLE SIM         ")
    print("========================================")
    
    player_hp = 100.0
    ai_hp = 100.0
    current_state = 0
    
    # Clear npz file to reset agent for testing
    if os.path.exists("../server/q_table.npz"):
        try:
            os.remove("../server/q_table.npz")
            print("[System] Cleared previous Memory. Hunter is vulnerable.")
        except Exception:
            pass
    
    actions_map = {0: "Idle", 1: "Chase", 2: "Dodge", 3: "Attack"}
    turn = 1
    ai_score = 0.0
    
    # Rich State context variables
    player_distance = 10 # 10 meters away
    
    def render_health(name, hp, adapted=None):
        blocks = int(max(0, hp) / 10)
        bar = "█" * blocks + "░" * (10 - blocks)
        adapt_str = f" (ADAPTED: {adapted})" if adapted else ""
        return f"[{name}]: {name_pad(name)}[{bar}] {int(hp)}/100 HP{adapt_str}"
        
    def name_pad(name):
        return " " * (9 - len(name))
        
    def get_hp_bucket(hp, is_ai):
        if is_ai:
            if hp <= 15: return 0
            if hp <= 30: return 1
            return 2
        else:
            if hp <= 15: return 0
            if hp <= 40: return 1
            return 2
    
    while player_hp > 0 and ai_hp > 0:
        print(f"\n--- TURN {turn} ---")
        
        # Last known adaptation (just to display something fun in UI if we have it)
        last_adaptation = None
        if os.path.exists("../server/q_table.npz") and turn > 1:
            try:
                import numpy as np
                data = np.load("../server/q_table.npz", allow_pickle=True)
                adapts = json.loads(str(data['adapted']))
                if adapts: last_adaptation = adapts[-1]
            except Exception: pass
            
        print(render_health("MAHORAGA", ai_hp, last_adaptation))
        print(render_health("USER", player_hp))
        print("-------------------------------------------------------")
        print("Choose an attack phenomenon (or 'quit'):")
        
        try:
            phenomenon = input("\nUser uses: ").strip().lower().replace(' ', '_')
        except EOFError:
            break
            
        if not phenomenon:
            continue
        if phenomenon in ['quit', 'exit', 'q']:
            print("Exiting battle simulation.")
            break
            
        if phenomenon == 'move_closer':
            player_distance = max(0, player_distance - 5)
            print(f">> Player moves closer. Distance is now {player_distance}m.")
            turn += 1
            continue
        elif phenomenon == 'move_away':
            player_distance += 5
            print(f">> Player moves away. Distance is now {player_distance}m.")
            turn += 1
            continue
            
        # Rich Context State Generation (Dual Health Sync)
        ai_bucket = get_hp_bucket(ai_hp, True)
        user_bucket = get_hp_bucket(player_hp, False)
        dist_cat = "close" if player_distance <= 5 else "far"
        
        current_state_str = f"{ai_bucket}_{user_bucket}_{dist_cat}"

        # Standard player damage
        base_damage = 10.0 # Changed to 10.0 based on new instructions
            
        # 1. Ask AI for an action
        act_payload = {
            "state": current_state_str,
            "phenomenon_id": phenomenon
        }
        
        try:
            act_res = requests.post(f"{SERVER_URL}/act", json=act_payload)
            action = act_res.json().get("action", 0)
        except Exception as e:
            print(f"Failed to connect: {e}\nIs rl_server.py running?")
            break
            
        action_name = actions_map.get(action, "Unknown")
        print(f"AI chose: {action_name.upper()}")
        
        damage_to_player = 0.0
        # Determine actual damage based on AI action
        if action == 2: # Dodge
            print(">> AI Dodges! (0 Damage taken)")
            base_damage = 0.0
        elif action == 3: # Attack
            damage_to_player = 15.0 # Changed to 15.0 per spec
            
        if action == 3 and base_damage > 0:
            print(">> Result: Both trade damage!")
            
        # 2. Simulate taking damage and updating Q-table
        next_state_str = current_state_str 
        
        is_player_dead = (player_hp - damage_to_player <= 0) # predictive check
        
        update_payload = {
            "state": current_state_str,
            "action": action,
            "next_state": next_state_str,
            "phenomenon_id": phenomenon,
            "damage_taken": base_damage,
            "damage_to_player": damage_to_player,
            "is_player_dead": is_player_dead,
            "ai_hp": ai_hp,
            "user_hp": player_hp,
            "turn": turn
        }
        
        try:
            update_res = requests.post(f"{SERVER_URL}/update", json=update_payload)
            result = update_res.json()
            
            eff_dmg = result.get('effective_damage', base_damage)
            ai_score += result.get('reward_applied', 0.0)
            
            # Apply effective damage to AI
            ai_hp -= eff_dmg
            
            if base_damage > 0 and eff_dmg == 0:
                print(f">> [System] Hunter is completely immune to {phenomenon}!")
            elif base_damage > 0 and eff_dmg < base_damage:
                print(f">> [System] Semantic immunity reduced damage to {eff_dmg}!")
                    
            if result.get("is_infused_counter"):
                print(f">>> 🔥 ADAPTIVE COUNTER! Unleashing {phenomenon.upper()}-INFUSED STRIKE! x2 DAMAGE! <<<")
                damage_to_player *= 2.0
                
            if damage_to_player > 0:
                player_hp -= damage_to_player
            
            if result.get("wheel_spin"):
                print(">> [System] 🛞 MAHORAGA WHEEL SPIN DETECTED! Adaptation achieved.")
                
            # Print Score
            score_txt = "Close to Victory!" if ai_score > 100 else "Struggling..." if ai_score < -50 else "Neutral"
            print(f">> AI Score: {int(ai_score)} ({score_txt})")
                
        except Exception as e:
            print(f"Failed to update server: {e}")
            break
            
        turn += 1

    if player_hp <= 0 and ai_hp <= 0:
        print("\n=== MUTUAL DESTRUCTION ===")
    elif player_hp <= 0:
        print("\n=== YOU DIED ===")
    elif ai_hp <= 0:
        print("\n=== HUNTER SLAIN ===")

if __name__ == "__main__":
    play_game()

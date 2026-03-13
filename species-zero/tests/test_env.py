import time
import json
import os
import random

SERVER_URL = "http://localhost:5000"

def render_map(distance):
    """Renders a 1D map showing AI and USER based on distance."""
    dots = max(0, int(distance))
    return f"[AI] {' . ' * dots}[USER] (Distance: {distance:.1f})"

def test_adaptation():
    print("--- Starting Species Zero Tactical Arena Simulator ---")
    
    current_distance = 10.0
    current_state = ""
    damage = 0.0
    user_hp = 100.0
    ai_hp = 100.0
    previous_phenomenon = None
    stunned = False
    sprint_count = 0
    
    # Clear npz file to reset agent for testing
    q_table_path = os.path.join(os.path.dirname(__file__), "../server/q_table.npz")
    if os.path.exists(q_table_path):
        os.remove(q_table_path)
        print("Cleared previous Q-table state.")
    
    turn = 1
    while user_hp > 0 and ai_hp > 0:
        penalty = (1.15 ** turn) / 100.0
        print(f"\n--- Turn {turn} (Pressure Level: {penalty:.3f}) ---")
        print(f"Player HP: {user_hp} | AI HP: {ai_hp}")
        print(render_map(current_distance))
        
        print("\nChoose an action (or type 'quit' to exit):")
        print("1. fire_spell (Ranged)")
        print("2. ice_spell (Ranged)")
        print("3. physical_punch (Melee)")
        print("Movement: [F]orward, [B]ackward, [S]tay")
        
        try:
            user_input = input("\nEnter attack choice: ").strip()
        except EOFError:
            break
            
        if not user_input:
            print("Invalid input. Please try again.")
            continue
            
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Exiting test bench.")
            break
            
        # Parse Movement
        user_action = "Idle"
        phenomenon = "none"
        if user_input.upper() in ['F', 'B']:
            if stunned:
                print("Player is STUNNED! Movement canceled.")
            else:
                user_action = "Moving"
                if user_input.upper() == 'F':
                    current_distance = max(0.0, current_distance - 1.5)
                elif user_input.upper() == 'B':
                    current_distance += 1.5
        elif user_input.upper() == 'S':
            user_action = "Idle"
        elif user_input == '1':
            phenomenon = "fire_spell"
            damage = 10.0
        elif user_input == '2':
            phenomenon = "ice_spell"
            damage = 10.0
        elif user_input == '3':
            phenomenon = "physical_punch"
            damage = 20.0
        else:
            # gracefully handle custom strings
            phenomenon = user_input.replace(' ', '_').lower()
            damage = 10.0
            
        # Clear stun condition after movement attempt
        stunned = False
            
        # Generate Dynamic Situational State: DistBucket_UserHPBucket_IncomingType_TurnPressure_LungeRange
        dist_bucket = "Close" if current_distance <= 2.0 else "Mid" if current_distance <= 6.0 else "Far"
        user_hp_bucket = "Healthy" if user_hp > 70 else "Wounded" if user_hp > 30 else "Critical"
        incoming_type = "Melee" if phenomenon == "physical_punch" else "None" if phenomenon == "none" else "Ranged"
        turn_pressure = "Critical" if turn > 25 else "Medium" if turn > 12 else "Low"
        lunge_range = "Lunge_Ready" if 1.5 < current_distance <= 3.5 else "No_Lunge"
        current_state = f"{dist_bucket}_{user_hp_bucket}_{incoming_type}_{turn_pressure}_{lunge_range}"

        # 1. Ask for an action
        act_payload = {
            "state": current_state,
            "phenomenon_id": phenomenon,
            "distance": current_distance,
            "user_action": user_action,
            "incoming_type": incoming_type,
            "turn_pressure": turn_pressure,
            "user_hp_bucket": user_hp_bucket,
            "lunge_range": lunge_range
        }
        
        print(f"\n[Player uses {phenomenon}]")
        print(f"Sending /act request: {act_payload}")
        try:
            act_res = requests.post(f"{SERVER_URL}/act", json=act_payload)
            action = act_res.json().get("action")
            print(f"AI chose action: {action}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            print("Did you start the flask server in another terminal? (python species-zero/server/rl_server.py)")
            break
            
        # Determine actual damage based on AI action
        damage_to_player = 0.0
        
        exhausted = sprint_count >= 2
        movement_mult = 0.5 if exhausted else 1.0
        
        if action in [7, 8]:
            sprint_count += 1
        else:
            sprint_count = 0
            
        if action == 1: # Advance
            dist_change = 1.5 * movement_mult
            current_distance = max(0.0, current_distance - dist_change)
            print(f"AI Advanced forward by {dist_change:.2f}! Distance is now {current_distance:.1f}")
            if exhausted:
                print("AI is Exhausted! Movement halved.")
        elif action == 2: # Dodge
            print("AI Dodged the attack! (No damage taken)")
            damage = 0.0
        elif action == 3: # Melee Attack
            if current_distance <= 1.5:
                damage_to_player = 20.0
                stunned = True # Apply Stun
                print(f"AI lands a devastating MELEE Strike! User is STUNNED!")
            else:
                print(f"AI whiffs a MELEE strike at {current_distance:.1f} distance!")
        elif action == 4: # Ranged Attack
            damage_to_player = 8.0
            print(f"AI fires a RANGED projectile!")
        elif action == 5: # Adapt Current
            print("AI focuses on actively adapting to the CURRENT attack!")
        elif action == 6: # Adapt Previous
            print("AI focuses on actively adapting to the PREVIOUS attack!")
        elif action == 7: # Blitz Assault
            dist_change = 2.0 * movement_mult
            current_distance = max(0.0, current_distance - dist_change)
            print(f"\033[1;31m[!!!] PREDATOR IS BLITZING!\033[0m")
            print(f"[AI] >>>>> [USER] (Closed distance by {dist_change:.2f})")
            if exhausted:
                print("AI is Exhausted! Movement halved.")

            if current_distance <= 1.5:
                damage_to_player = 25.0
                stunned = True # Apply Stun
                print("AI lands a devastating BLITZ Strike! User is STUNNED!")
            else:
                print(f"AI whiffs a BLITZ strike at {current_distance:.1f} distance!")
        elif action == 8: # Evasive Skirmish
            if current_distance > 3.0:
                print("AI performs an Evasive Skirmish!")
                damage_to_player = 10.0
                if random.random() < 0.8:
                    print("AI Dodged the attack successfully! (No damage taken)")
                    damage = 0.0
                else:
                    print("AI failed to dodge during the Skirmish!")
            else:
                print("AI attempted an Evasive Skirmish but was too close!")
            
        # 2. Simulate taking damage and updating Q-table
        update_payload = {
            "state": current_state,
            "action": action,
            "next_state": current_state,
            "phenomenon_id": phenomenon,
            "previous_phenomenon_id": previous_phenomenon,
            "distance": current_distance,
            "user_action": user_action,
            "incoming_type": incoming_type,
            "turn_pressure": turn_pressure,
            "user_hp_bucket": user_hp_bucket,
            "lunge_range": lunge_range,
            "damage_taken": damage,
            "damage_to_player": damage_to_player,
            "is_player_dead": (user_hp - damage_to_player <= 0),
            "user_hp": user_hp,
            "ai_hp": ai_hp,
            "turn": turn
        }
        print(f"AI took {damage} damage from {phenomenon}. Sending /update request...")
        
        try:
            update_res = requests.post(f"{SERVER_URL}/update", json=update_payload)
            result = update_res.json()
            
            print(f"Server Response: {json.dumps(result, indent=2)}")
            
            infused = result.get("is_infused_counter", False)
            multiplier = result.get("infused_multiplier", 1.0)
            if infused:
                print(f"🔥 AI COUNTERED WITH INFUSED STRIKE! (Damage x{multiplier:.1f})")
                damage_to_player *= multiplier
            
            if 'effective_damage' in result:
                ai_hp -= result['effective_damage']
            user_hp -= damage_to_player
            
            if result.get("wheel_spin"):
                print("🛞 MAHORAGA WHEEL SPIN DETECTED! AI adapted to this attack.")
                
            if user_hp <= 0:
                print("💀 USER DIED! AI Wins!")
        except Exception as e:
            print(f"Failed to update server: {e}")
            
        previous_phenomenon = phenomenon
        turn += 1

if __name__ == "__main__":
    test_env_installed = True
    try:
        import requests
    except ImportError:
        print("Please install requests: pip install requests")
        test_env_installed = False
        
    if test_env_installed:
        test_adaptation()

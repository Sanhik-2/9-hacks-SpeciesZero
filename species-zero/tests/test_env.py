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
    consecutive_retreats = 0 # Anti-Kiting tracking
    suppressed_phenomena = {} # phenomenon_id -> turns left
    
    # Clear npz file to reset agent for testing
    q_table_path = os.path.join(os.path.dirname(__file__), "../server/q_table.npz")
    if os.path.exists(q_table_path):
        os.remove(q_table_path)
        print("Cleared previous Q-table state.")
    
    turn = 1
    while user_hp > 0 and ai_hp > 0:
        penalty = min((1.15 ** turn) / 100.0, 0.5)
        print(f"\n--- Turn {turn} (Pressure Level: {penalty:.3f}) ---")
        
        # UI Overhaul: Flash AI HP in Red if in Phase 2
        ai_hp_display = f"{ai_hp:.1f}"
        if ai_hp <= 30:
            ai_hp_display = f"\033[1;31m{ai_hp:.1f} [PHASE 2: RESURRECTION]\033[0m"
            
        print(f"Player HP: {user_hp:.1f} | AI HP: {ai_hp_display}")
        
        # UI Overhaul: Distance symbols
        map_str = render_map(current_distance)
        if current_distance <= 2.0:
            map_str = map_str.replace(" . ", " 🔥💀🔥 ")
        print(map_str)
        
        # Decrement suppression timers
        for phenom in list(suppressed_phenomena.keys()):
            suppressed_phenomena[phenom] -= 1
            if suppressed_phenomena[phenom] <= 0:
                del suppressed_phenomena[phenom]
                print(f"[*] Identity Suppression cleared for {phenom.upper()}.")

        print("\nChoose an action (or type 'quit' to exit):")
        print("1. attack (Standard Pressure)")
        print("2. block (Defensive Posture)")
        print("3. ambush (High-Damage Lunge)")
        print("4. counterattack (Reactive Strike)")
        print("5. dodge (Evasive Maneuver)")
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
                    consecutive_retreats = 0
                elif user_input.upper() == 'B':
                    current_distance += 1.5
                    consecutive_retreats += 1
        elif user_input.upper() == 'S':
            user_action = "Idle"
            consecutive_retreats = 0
        elif user_input == '1':
            phenomenon = "attack"
            if current_distance <= 3.0:
                damage = 15.0
            else:
                damage = 0.0
                print(f"Your attack missed! Too far ({current_distance:.1f} units). Get closer!")
        elif user_input == '2':
            phenomenon = "block"
            damage = 0.0
        elif user_input == '3':
            phenomenon = "ambush"
            if current_distance <= 6.0:
                damage = 25.0
            else:
                damage = 0.0
                print(f"Your ambush missed! Too far ({current_distance:.1f} units). Need to be within 6.0!")
        elif user_input == '4':
            phenomenon = "counterattack"
            if current_distance <= 3.0:
                damage = 15.0
            else:
                damage = 0.0
                print(f"Your counterattack missed! Too far ({current_distance:.1f} units). Get closer!")
        elif user_input == '5':
            phenomenon = "dodge"
            damage = 0.0
        else:
            # gracefully handle custom strings
            phenomenon = user_input.replace(' ', '_').lower()
            if current_distance <= 4.0:
                damage = 10.0
            else:
                damage = 0.0
                print(f"Your attack missed! Too far ({current_distance:.1f} units).")
            
        # Identity Suppression Check
        if phenomenon in suppressed_phenomena:
            print(f"\033[1;35m[!] YOUR POWER IS FADING. Damage with {phenomenon.upper()} reduced by 50%.\033[0m")
            damage *= 0.5
            
        # Clear stun condition after movement attempt
        stunned = False
            
        # Generate Dynamic Situational State: DistBucket_UserHPBucket_IncomingType_TurnPressure_LungeRange
        dist_bucket = "Close" if current_distance <= 2.0 else "Mid" if current_distance <= 6.0 else "Far"
        user_hp_bucket = "Healthy" if user_hp > 70 else "Wounded" if user_hp > 30 else "Critical"
        incoming_type = "Melee" if phenomenon in ["attack", "ambush", "counterattack"] else "None" if phenomenon in ["none", "block", "dodge"] else "Ranged"
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
            "lunge_range": lunge_range,
            "ai_hp": ai_hp
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
        
        # Anti-Kiting: Triple Advance if User moves Backward twice
        if consecutive_retreats >= 2:
            movement_mult *= 3.0
            print("\033[1;34m[!] PREY IS RETREATING. PREDATOR IS CLOSING THE GAP FAST!\033[0m")
        
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
        elif action == 6: # Mirror Engine (Mimicry)
            print("AI focuses on Mirroring your phenomenon!")
        elif action == 7: # Shadow Lunge (Redefinition)
            if current_distance <= 6.0:
                print(f"\033[1;31m[!!!] SHADOW LUNGE: PREDATOR TELEPORTED TO YOU!\033[0m")
                current_distance = 0.0
                damage_to_player = 25.0
                stunned = True
                print("AI lands a devastating SHADOW LUNGE Strike! User is STUNNED!")
            else:
                print(f"AI attempted a SHADOW LUNGE but you were too far ({current_distance:.1f} units)!")
                # Optional: still advance a bit if too far? User didn't specify, I'll stick to strict logic.
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
                
            if result.get("mockery_flag"):
                target = result.get("mockery_target", "magic")
                print(f"\033[1;33m[!] SPECIES ZERO IS MOCKING YOUR {target.upper()}!\033[0m")
                print("\033[1;35m[!] YOUR POWER IS FADING. SPECIES ZERO HAS CONSUMED YOUR ESSENCE.\033[0m")
                # Action 6 deals 1.5x of the mirrored spell damage? User said 1.5x damage multiplier.
                # Assuming base spell damage is 10.0 (from 1, 2) or whatever last was.
                # Actually, Mirror Engine is Mirror of the phenomenon most used.
                damage_to_player = 15.0 # 10.0 * 1.5
                # Apply Identity Suppression for 3 turns
                suppressed_phenomena[target] = 3
            
            if 'effective_damage' in result:
                ai_hp -= result['effective_damage']
            user_hp -= damage_to_player
            
            if result.get("wheel_spin"):
                print("🛞 MAHORAGA WHEEL SPIN DETECTED! AI adapted to this attack.")
                
            if user_hp <= 0:
                print("\033[1;31m💀 USER DIED! AI Wins!\033[0m")
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

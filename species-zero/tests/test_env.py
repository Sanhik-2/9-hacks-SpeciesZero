import time
import json
import os
import random

SERVER_URL = "http://localhost:5000"

def test_adaptation():
    print("--- Starting Species Zero Interactive Test Bench ---")
    
    current_state = 0
    damage = 10.0
    user_hp = 100.0
    ai_hp = 100.0
    previous_phenomenon = None
    
    # Clear npz file to reset agent for testing
    q_table_path = os.path.join(os.path.dirname(__file__), "../server/q_table.npz")
    if os.path.exists(q_table_path):
        os.remove(q_table_path)
        print("Cleared previous Q-table state.")
    
    turn = 1
    while user_hp > 0 and ai_hp > 0:
        print(f"\n--- Turn {turn} ---")
        print(f"Player HP: {user_hp} | AI HP: {ai_hp}")
        print("Choose an attack phenomenon (or type 'quit' to exit):")
        print("1. fire_spell")
        print("2. ice_spell")
        print("3. physical_punch")
        print("Or type any custom phenomenon_id")
        
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
            
        if user_input == '1':
            phenomenon = "fire_spell"
        elif user_input == '2':
            phenomenon = "ice_spell"
        elif user_input == '3':
            phenomenon = "physical_punch"
        else:
            # gracefully handle custom strings
            phenomenon = user_input.replace(' ', '_').lower()
            
        # Generate Dynamic Situational State
        distance = random.choice(["Close", "Mid", "Far"])
        user_action = random.choice(["Idle", "Attacking", "Moving"])
        hp_status = "LowHP" if ai_hp < 30 else "HighHP"
        current_state = f"{distance}_{hp_status}_{user_action}"

        # 1. Ask for an action
        act_payload = {
            "state": current_state,
            "phenomenon_id": phenomenon,
            "distance": distance,
            "user_action": user_action
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
        if action == 2: # Dodge
            print("AI Dodged the attack! (No damage taken)")
            damage = 0.0
        elif action == 3: # Attack
            damage_to_player = 20.0
            print(f"AI Strikes back against the Player!")
        elif action == 4: # Adapt Current
            print("AI focuses on actively adapting to the CURRENT attack!")
        elif action == 5: # Adapt Previous
            print("AI focuses on actively adapting to the PREVIOUS attack!")
            
        # 2. Simulate taking damage and updating Q-table
        update_payload = {
            "state": current_state,
            "action": action,
            "next_state": current_state,
            "phenomenon_id": phenomenon,
            "previous_phenomenon_id": previous_phenomenon,
            "distance": distance,
            "user_action": user_action,
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
            
            if 'effective_damage' in result:
                ai_hp -= result['effective_damage']
            user_hp -= damage_to_player
            
            if result.get("wheel_spin"):
                print("🛞 MAHORAGA WHEEL SPIN DETECTED! AI adapted to this attack.")
                
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

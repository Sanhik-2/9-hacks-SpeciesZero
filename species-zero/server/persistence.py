import json
import os

def save_state(q_table_dict, adapted_phenomena, adaptation_registry, consecutive_wins, global_combat_timer, filepath):
    """Saves Q-table and adaptation data to a JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump({
                'q_table': q_table_dict,
                'adapted_phenomena': list(adapted_phenomena),
                'adaptation_registry': adaptation_registry,
                'consecutive_wins': consecutive_wins,
                'global_combat_timer': global_combat_timer
            }, f, indent=4)
    except Exception as e:
        print(f"Error saving state to {filepath}: {e}")

def load_state(filepath):
    """Loads Q-table and adaptation data, returning empty defaults if none exist."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return (
                data.get('q_table', {}),
                set(data.get('adapted_phenomena', [])),
                data.get('adaptation_registry', {}),
                data.get('consecutive_wins', 0),
                data.get('global_combat_timer', 0)
            )
        except Exception as e:
            print(f"Warning: Failed to load state from {filepath}: {e}")
    return {}, set(), {}, 0, 0


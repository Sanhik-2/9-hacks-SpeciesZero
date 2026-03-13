import numpy as np
import os
import json

def save_state(q_table_dict, adapted_phenomena, adaptation_registry, filepath):
    """Saves Q-table and adaptation data to an .npz file."""
    np.savez(filepath, 
             q_table=json.dumps(q_table_dict), 
             adapted_phenomena=json.dumps(list(adapted_phenomena)),
             adaptation_registry=json.dumps(adaptation_registry))

def load_state(filepath):
    """Loads Q-table and adaptation data, returning empty defaults if none exist."""
    if os.path.exists(filepath):
        try:
            data = np.load(filepath, allow_pickle=True)
            # numpy saves these as 0-d arrays, need to extract the string item first
            q_table_str = str(data['q_table'].item()) if data['q_table'].shape == () else str(data['q_table'])
            adapted_str = str(data['adapted_phenomena'].item()) if data['adapted_phenomena'].shape == () else str(data['adapted_phenomena'])
            registry_str = str(data['adaptation_registry'].item()) if data['adaptation_registry'].shape == () else str(data['adaptation_registry'])
            
            q_table_dict = json.loads(q_table_str)
            adapted_phenomena = set(json.loads(adapted_str))
            adaptation_registry = json.loads(registry_str)
            return q_table_dict, adapted_phenomena, adaptation_registry
        except Exception as e:
            print(f"Warning: Failed to load state from {filepath}: {e}")
            pass
    return {}, set(), {}

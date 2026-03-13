# Species Zero

A full-stack project featuring a Mahoraga-style AI in Unity that adapts to player behavior using a local Python RL (Q-Learning) backend.

## Architecture & Features
- **The Mahoraga Engine**: Adapts to player tactics completely after 3 hits.
- **Semantic Adaptation**: String-similarity checks give partial immunity (50%) to variations of known attacks (e.g., `fire_ball` vs `fire_spell`).
- **Aggressive Hunter Rewards**: The RL brain prioritizes dealing damage to the player over avoiding damage.
- **Persistence**: NPZ save/load engine guarantees continuity across sessions.

## Project Structure
- `server/`: Python Flask Backend.
- `unity-client/`: C# Scripts for Unity integration.
- `tests/`: Terminal-based battle simulator.

## Requirements
- Python 3.8+
- Flask
- NumPy
- Requests (for the test bench)

Install dependencies:
```bash
pip install flask numpy requests
```

## Running the Battle Simulator
To verify the core AI adaptation logic without the Unity client:

1. **Start the Flask Server**
   Open a terminal and run:
   ```bash
   cd species-zero/server
   python rl_server.py
   ```
   The Flask server should start on `http://localhost:5000`.

2. **Run the Battle Simulator**
   Open a second terminal and run:
   ```bash
   cd species-zero/tests
   python battle_sim.py
   ```
   You will engage in a text-based battle against the Hunter. Try attacking repeatedly with the same phenomenon, and try using semantically similar attacks (like `ice_blast` then `ice_bolt`) to see the Mahoraga logic in action!

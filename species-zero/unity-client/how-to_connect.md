# Species Zero: How-to-Connect Guide

This guide explains how to set up the 3D combat system and connect the Unity C# Controller to the Python RL API.

## 1. Setting the API Endpoint
1. Open your Unity scene.
2. Select the **AI Agent** GameObject.
3. Attach the `SpeciesZeroController.cs` script to it.
4. In the Inspector, locate the **Server Url** field.
5. Set it to the address where your Python server is running (default: `http://localhost:5000`).

## 2. NavMesh Configuration
To ensure the AI understands 3D spatial reasoning and can navigate the environment:
1. Open the **Navigation** window in Unity (**Window > AI > Navigation**).
2. Mark your ground and obstacles as **Static**.
3. In the **Bake** tab, click **Bake** to generate the NavMesh surface.
4. Ensure the AI Agent has a `NavMeshAgent` component attached (the `SpeciesZeroController` will automatically try to find it).

## 3. Component References
In the `SpeciesZeroController` component within the Unity Inspector, assign the following:
- **Player Transform**: The Transform of your main player character.
- **Animator**: The Animator component responsible for AI animations.
- **Mahoraga Wheel**: The `MahoragaWheel` script if using the adaptation visuals.
- **Glitch Effect**: A ParticleSystem for the `identity_suppressed` visual.
- **Ascended Model**: Set the Mesh and Material for the Phase 2 transformation.

## 4. Running the System
1. Start the Python server: `python rl_server.py`.
2. Enter **Play Mode** in Unity.
3. The AI will begin sending spatial telemetry every 0.1s and receiving combat actions.

# Species Zero: Neural Dopamine Visuals

Your friend on the Python server side has implemented the "Neural Dopamine" system, and it is now streaming a raw `dopamine_level` (ranging from 1.0 to 5.0) heavily influencing AI aggression.

You need to hook this up to the visual/animation stack on the Unity side. Here's what to do:

### 1. The Glitch Intensity
Use the `dopamine_level` (1.0 to 5.0) to drive a Chromatic Aberration or Lens Distortion effect in Unity Post Processing. 
- Higher Dopamine = Intense visual distortion. The "high" shouldn't just be an internal number; it should literally warp the player's screen as the AI gets hyped.

### 2. The Animation Speed
Multiply the AI's animation speed by `(1 + (dopamine_level * 0.1))`.
- When dopamine is high, the AI should look visibly jittery and move noticeably faster.

### 3. The Death Blow
When `dopamine_level > 3.0`, activate red particles emitting from the AI's hands. 
- This serves as the primary visual cue to the player that the AI has reached "Killer Mode" and will aggressively pursue until death.

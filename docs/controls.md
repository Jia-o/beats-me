# beats-me — Feature Activation Guide

> **What you do with your hands and what you say to control every feature.**

---

## Modes

beats-me has two modes, each activated from the launch screen that appears when you run `python main.py`.

| Mode | Playlist | Hand controls | Voice controls |
|---|---|---|---|
| **Personal Mode** | Your personal playlist | ✅ Full gesture set | ❌ Not available |
| **Staff Mode** | Staff playlist | ✅ Full gesture set | ❌ Not available |

---

## Selecting a Mode

### Hand activation
1. Run `python main.py`.  
2. The launch screen shows two mode cards.  
3. Move your mouse pointer to the card you want and **click the green "Select" button** on the right side of the card.

### Voice activation
Voice-based mode switching is **not implemented**. You must use the mouse/trackpad to pick a mode.

---

## Returning to the Mode-Selection Screen

### Hand activation (keyboard)
While the camera view is open, press the **`M` key** on your keyboard.  
This stops the camera, pauses music, and takes you back to the launch screen.

### Voice activation
Not available — only the `M` key works for navigation.

---

## Playback Controls (Personal Mode & Staff Mode)

All gesture controls use your webcam. Make sure your hand is clearly visible in the camera frame before performing a gesture. A 1.25-second cooldown applies between gestures to prevent double-firing.

---

### Play / Pause (toggle)

**Hand gesture**
1. Hold your hand open in front of the camera, palm roughly facing the lens.
2. Slowly bring your **thumb tip and index fingertip together** until they touch (a "pinch").  
3. Hold the pinch closed for about **4 camera frames** (~0.13 s at 30 fps) — you will feel/see the command fire.  
4. Open your hand back to the resting position before attempting the next gesture.

*The pinch is a toggle: one pinch pauses, the next pinch plays.*

**Voice activation**  
Not supported in either mode. Use the hand pinch gesture.

---

### Skip to Next Track

**Hand gesture**
1. Hold your hand relaxed in front of the camera.
2. Extend your **index and middle fingers upward** (forming a "V" or peace sign) while keeping your ring and pinky fingers curled down.
3. **Hold the V-shape to the right side of the frame** (hand centroid past ~60 % of the frame width) for about **18 camera frames** (~0.6 s at 30 fps) — the next-track command fires after the crossfade (~450 ms).

*The V-shape must be held in position, not swiped. Make sure your ring and pinky fingers remain clearly curled.*

**Voice activation**  
Not supported. Use the V-shape hand gesture.

---

### Go to Previous Track

**Hand gesture**  
Same as "Skip to Next Track" but hold the V-shape on the **left side of the frame** (hand centroid below ~40 % of the frame width) instead.

**Voice activation**  
Not supported. Use the V-shape hand gesture.

---

### Volume Up

**Hand gesture**
1. Curl your middle, ring, and pinky fingers inward (closed fist except for the index finger).  
2. Extend only your **index finger, pointing straight upward**, so the fingertip is clearly above the wrist by at least ~15 % of the frame height.  
3. **Hold this pointing-up pose** for about **18 camera frames** (~0.6 s at 30 fps) — the first volume tick (+3 %) fires.  
4. Keep holding and volume increases another **+3 % every ~45 frames** (~1.5 s) until you lower your finger.

**Voice activation**  
Not supported. Use the hand pointing gesture.

---

### Volume Down

**Hand gesture**  
Same as "Volume Up" but point your **index finger straight downward**, so the fingertip is clearly below the wrist by at least ~8 % of the frame height, with the other fingers not extended downward.  
Hold the pose the same way — first tick fires after ~18 frames, then repeats every ~45 frames (−3 % each tick).

**Voice activation**  
Not supported. Use the hand pointing gesture.

---

## Debug and Developer Tools

These keyboard shortcuts are available while the camera view is open:

| Key | Hand action | What it does |
|---|---|---|
| `D` | Press the **D** key | Toggle the **debug panel** (shows raw gesture classification data) |
| `L` | Press the **L** key | Toggle the **event-log panel** (shows timestamped command history) |

**Voice activation:** Not available — use the keyboard.

---

## Feature Summary

| Feature | Hand activation | Voice activation |
|---|---|---|
| Select a mode | Click "Select" button | ❌ Not available |
| Return to mode selection | Press `M` key | ❌ Not available |
| Play / Pause | Pinch (thumb + index tip) | ❌ Not available |
| Skip to next track | V-shape right (hold) | ❌ Not available |
| Go to previous track | V-shape left (hold) | ❌ Not available |
| Volume up | Point index finger up, hold | ❌ Not available |
| Volume down | Point index finger down, hold | ❌ Not available |
| Debug panel | Press `D` key | ❌ Not available |
| Event log panel | Press `L` key | ❌ Not available |

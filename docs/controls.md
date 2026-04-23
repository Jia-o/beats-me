# beats-me — Feature Activation Guide

> **What you do with your hands and what you say to control every feature.**

---

## Modes

beats-me has two modes, each activated from the launch screen that appears when you run `python main.py`.

| Mode | Playlist | Hand controls | Voice controls |
|---|---|---|---|
| **Personal Mode** | Your personal playlist | ✅ Full gesture set | ❌ Not available |
| **Staff Mode** | Staff playlist | ✅ Full gesture set | ✅ Announcement pause/resume |

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
1. Hold your hand relaxed and open in front of the camera.  
2. In one brisk, continuous motion, **sweep your whole hand to the right** — aim to travel roughly one-third of the camera frame width within about **0.5 seconds**.  
3. Let your hand settle; the next track should begin after the crossfade (~450 ms).

*The swipe is measured by wrist/palm centroid velocity. A slow drift will not trigger it — the motion must be quick and deliberate.*

**Voice activation**  
Not supported. Use the hand swipe gesture.

---

### Go to Previous Track

**Hand gesture**  
Same as "Skip to Next Track" but sweep your hand **to the left** instead.

**Voice activation**  
Not supported. Use the hand swipe gesture.

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

## Announcement Pause / Resume (Staff Mode only)

Staff Mode listens continuously for speech via the microphone using offline speech recognition ([Vosk](https://alphacephei.com/vosk/)). No push-to-talk button is needed — it is always listening.

There are two voice-driven behaviours that layer on top of each other:

1. **Volume Ducking** – fires on *any* detected speech.
2. **Announcement Pause** – fires only when a specific trigger phrase is recognised.

### Voice activation

**Prerequisites (one-time setup)**

1. Download a Vosk speech model for your language, e.g.  
   [`vosk-model-small-en-us-0.15`](https://alphacephei.com/vosk/models) (~40 MB).  
2. Unzip the model folder somewhere on disk (e.g. `models/vosk-model-small-en-us-0.15`).  
3. Open `config.py` and set `VOSK_MODEL_PATH` to that folder path:
   ```python
   VOSK_MODEL_PATH = "models/vosk-model-small-en-us-0.15"
   ```
4. Make sure the `vosk` and `sounddevice` packages are installed:
   ```bash
   pip install vosk sounddevice
   ```
5. Grant the app access to your microphone when your OS prompts for permission (or pre-allow it in System Settings → Privacy → Microphone).

**Volume Ducking (any speech)**

Whenever the microphone picks up any speech:
- Volume **immediately drops to 15 %**.
- Once you **stop speaking** (approximately **1.7 seconds of silence**), the volume **smoothly recovers** to the level it was at before ducking — incrementing **+5 % every 200 ms** for a professional fade-in effect.

**Announcement Pause (trigger phrase)**

If you say one of the configured trigger phrases:

- **"everyone listen up for a sec"**
- **"everyone listen up"**

the music **pauses** completely (it will already be at 15 % from ducking). After approximately **1.7 seconds of silence**, music **resumes** and the volume **smoothly recovers** to its original level.

The system performs a simple substring match, so you do not need to say the phrase in isolation — it can be part of a longer sentence.

**What if voice is not working?**

If `VOSK_MODEL_PATH` is not set or the `vosk`/`sounddevice` packages are missing, the voice feature silently disables itself. A message is printed to the console:

```
[voice] announcement listener disabled: VOSK_MODEL_PATH not set in config.py
```

In that case, Staff Mode still works with hand gestures only.

### Hand activation  
There is no hand gesture equivalent for announcement pause/resume — this feature is **voice-only**.

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
| Skip to next track | Swipe right (quick) | ❌ Not available |
| Go to previous track | Swipe left (quick) | ❌ Not available |
| Volume up | Point index finger up, hold | ❌ Not available |
| Volume down | Point index finger down, hold | ❌ Not available |
| Volume ducking to 15 % *(Staff Mode)* | ❌ Not available | Any speech detected |
| Smooth volume recovery *(Staff Mode)* | ❌ Not available | Silence for ~1.7 s |
| Announcement pause *(Staff Mode)* | ❌ Not available | Say trigger phrase |
| Announcement resume + recover *(Staff Mode)* | ❌ Not available | Silence for ~1.7 s |
| Debug panel | Press `D` key | ❌ Not available |
| Event log panel | Press `L` key | ❌ Not available |

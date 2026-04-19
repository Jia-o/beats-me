# beats-me

Control Spotify playback through movement and gestures using your webcam.

## Modes

| Mode | Trigger | Actions |
|---|---|---|
| **Conductor** | Hand gestures | Pinch = play/pause · Swipe left/right = prev/next · Point up/down = volume |
| **Focus** | Body posture | Head down = focus playlist · Upright = energise playlist · Gone = pause |
| **Emotion** | Facial expression | Smile = upbeat playlist · Frown = moody playlist |

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Spotify credentials to .env
#    (create the file if it doesn't exist)
cat > .env <<'EOF'
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
EOF

# 4. Add your playlist IDs to config.py
#    (search for the YOUR_*_PLAYLIST_ID placeholders)

# 5. Run
python main.py
```

The first run opens a browser for Spotify OAuth. After authorising, a
`.cache` file is written so subsequent runs skip the browser step.

## Controls

| Key | Effect |
|---|---|
| **M** | Return to mode-selection screen (works from both windows) |

## Testing without Spotify

If the `.env` file is missing or credentials are invalid the app automatically
falls back to `spotify/mock_controller.py`, which prints every action to the
console so you can verify the vision logic without a Spotify account.

## Project layout

```
main.py              Entry point & global state
config.py            Credentials, constants, playlist ID placeholders
spotify/
  controller.py      Spotipy wrapper (threaded, error-handled)
  mock_controller.py Console-print fallback for credential-free testing
perception/
  engine.py          Abstract base for all perception engines
  hands.py           Gesture detection  (Conductor Mode)
  pose.py            Posture detection  (Focus Mode)
  face.py            Emotion detection  (Emotion Mode) via Face Mesh
modes/
  conductor_mode.py  Gesture  → Spotify action
  focus_mode.py      Posture  → playlist / pause
  emotion_mode.py    Emotion  → playlist
ui/
  selection_screen.py  Splash / mode-picker (CTk root window)
  camera_view.py       Live camera feed with MediaPipe overlays (CTkToplevel)
```
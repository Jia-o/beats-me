# beats me

Control Spotify playback and data through hand gestures using your webcam.

## Setup
```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Spotify credentials to .env
#    (create the file if it doesn't exist)
cat > .env <<'EOF'
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
EOF

# 4. Replace my playlists with yours in config.py

# 4. Run
python main.py
```

---

## Codebase Architecture – File Summaries

| File | What it controls |
|---|---|
| `main.py` | Application entry point. Builds the Spotify controller (real or mock), shows the mode-selection screen, and launches `CameraView` with the chosen mode. |
| `config.py` | All runtime constants: Spotify credentials (loaded from `.env`), camera index & resolution, gesture thresholds (pinch hold frames, swipe velocity, point hold frames, volume step), and event-log size. |
| `modes/personal_mode.py` | Personal Mode handler. Maps recognised hand-gesture commands (`toggle_play`, `next`, `prev`, `vol_up`, `vol_down`) to Spotify controller calls. Also exposes `get_theme_color()` for the dynamic border. |
| `modes/staff_mode.py` | Staff Mode handler. Maps recognised hand-gesture commands (`toggle_play`, `next`, `prev`, `vol_up`, `vol_down`) to Spotify controller calls. Also exposes `get_theme_color()` for the dynamic border. |
| `perception/engine.py` | Abstract base class (`PerceptionEngine`) for all perception back-ends. Manages the `start` / `stop` lifecycle and the `active` flag. |
| `perception/hands.py` | `HandsEngine` – MediaPipe Task-based hand-landmark detection. Classifies four gestures (pinch, swipe left/right, point up/down) with hold-frame debouncing and a cooldown gate. Exposes both a confirmed `command` and a `pending` pre-fire label in the result dict. |
| `perception/_models.py` | Download-and-cache utility for MediaPipe `.task` model files. Stores models under `.cache/`. |
| `ui/camera_view.py` | `CameraView` Tkinter window. Runs a daemon camera thread that captures frames, processes them through the active engine, draws the **Visual Feedback Overlay** (hand-present / pending / confirmed gesture) and the **Dynamic Theme Border**, then hands the result to the mode handler. The Tk event loop polls the frame queue at ~30 fps and refreshes the theme colour every 5 seconds. |
| `ui/selection_screen.py` | `SelectionScreen` – the launch-screen UI showing the Personal and Staff mode cards. |
| `spotify/controller.py` | `SpotifyController` – wraps Spotipy for real Spotify control. Provides: playback (play, pause, skip, previous), volume control (`set_volume`, `adjust_volume`), crossfade skipping, and **dynamic theming** (`get_theme_color` backed by a background audio-features poller). |
| `spotify/mock_controller.py` | `MockSpotifyController` – drop-in stub that prints every action to the console. Used automatically when no valid Spotify credentials are found. Includes stubs for all new methods. |

---

## Controls

For full physical activation instructions for every feature, see **[docs/controls.md](docs/controls.md)**.

### Quick reference

#### Choosing a mode
On the launch screen, **click the green "Select" button** on the mode card you want.  
*(Voice-based mode switching is not implemented.)*

#### Hand gestures — Personal Mode & Staff Mode

| What you do with your hand | What happens |
|---|---|
| Bring thumb tip and index fingertip together (pinch), hold briefly | Toggle **Play / Pause** |
| Rapid rightward hand sweep across the camera view | **Skip** to next track |
| Rapid leftward hand sweep across the camera view | **Previous** track |
| Extend only index finger pointing **upward**, hold the pose | **Volume up** (+3 % per tick, repeats while held) |
| Extend only index finger pointing **downward**, hold the pose | **Volume down** (−3 % per tick, repeats while held) |

#### Keyboard shortcuts (camera view)

| Key | Action |
|---|---|
| `M` | Return to mode-selection screen |
| `D` | Toggle debug panel |
| `L` | Toggle event-log panel |
# beats me

Control Spotify playback through movement and gestures using your webcam.

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

#### Voice — Staff Mode only

| What you say | What happens |
|---|---|
| *"everyone listen up for a sec"* | Music **pauses** for the announcement |
| *"everyone listen up"* | Music **pauses** for the announcement |
| *(silence for ~1.7 s after speaking)* | Music **resumes** automatically |

> Voice requires a [Vosk](https://alphacephei.com/vosk/) model and `VOSK_MODEL_PATH` set in `config.py`.  
> See [docs/controls.md](docs/controls.md) for setup details.

#### Keyboard shortcuts (camera view)

| Key | Action |
|---|---|
| `M` | Return to mode-selection screen |
| `D` | Toggle debug panel |
| `L` | Toggle event-log panel |
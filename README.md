# beats me

Control Spotify playback through movement and gestures using your webcam.

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

# 4. Replace my playlists with yours in config.py

# 4. Run
python main.py
```
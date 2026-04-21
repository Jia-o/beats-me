import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Spotify credentials (populated from .env)
# ---------------------------------------------------------------------------
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")

# ---------------------------------------------------------------------------
# Playlist IDs – replace these with real Spotify playlist IDs
# ---------------------------------------------------------------------------
PLAYLIST_FOCUS    = "37i9dQZF1EIfjzgnbx4yqL"  # Focus Mode: head down / studying
PLAYLIST_ENERGIZE = "37i9dQZF1EIgG2NEOhqsD7"  # Focus Mode: upright / energized
PLAYLIST_MOODY    = "37i9dQZF1EIhmSBwUDxg84"  # Emotion Mode: sad
PLAYLIST_UPBEAT   = "37i9dQZF1EVJHK7Q1TBABQ"  # Emotion Mode: happy

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# ---------------------------------------------------------------------------
# Conductor Mode – gesture thresholds
# ---------------------------------------------------------------------------
# Pinch: normalized Euclidean distance between thumb tip and index tip
PINCH_THRESHOLD = 0.05
# Pinch hold: consecutive frames the pinch must be held before firing
PINCH_HOLD_FRAMES = 4

# Swipe: track wrist x over this many frames; fire if total displacement exceeds threshold
SWIPE_FRAMES = 12
SWIPE_THRESHOLD = 0.18          # Minimum normalized horizontal displacement

# Point hold: frames the index finger must be held up/down before first trigger
POINT_HOLD_FRAMES = 18
# Point repeat: once triggered, fire again every N frames while still held
POINT_REPEAT_INTERVAL = 30

# Volume step per point trigger (percentage points, signed by direction)
VOLUME_STEP = 10

# ---------------------------------------------------------------------------
# Focus Mode – pose thresholds
# ---------------------------------------------------------------------------
# Head down: nose-to-shoulder offset below this ratio (normalized coords)
HEAD_DOWN_RATIO = 0.15
# Gone: frames without a detected pose before switching to "gone"
GONE_TIMEOUT = 90
# Posture stable: consecutive frames the same posture must be held before emitting
POSTURE_STABLE_FRAMES = 10

# ---------------------------------------------------------------------------
# Emotion Mode – face mesh thresholds
# ---------------------------------------------------------------------------
# Smile/frown: mouth-corner elevation relative to lip center (normalized coords)
SMILE_THRESHOLD = 0.008
# Emotion stable: consecutive frames the same emotion must be held before emitting
EMOTION_STABLE_FRAMES = 15

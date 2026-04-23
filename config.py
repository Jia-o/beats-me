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
PERSONAL_PLAYLIST = "37i9dQZF1EIfjzgnbx4yqL"  # Personal mode playlist
STAFF_PLAYLIST    = "37i9dQZF1EIfjzgnbx4yqL"  # Staff mode playlist

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# ---------------------------------------------------------------------------
# Hands – gesture thresholds
# ---------------------------------------------------------------------------
# Pinch: normalized Euclidean distance between thumb tip and index tip
PINCH_THRESHOLD = 0.05
# Pinch hold: consecutive frames the pinch must be held before firing
PINCH_HOLD_FRAMES = 4

# Swipe (burst detection, normalized by palm scale)
SWIPE_BURST_MIN_DISPLACEMENT = 0.35
SWIPE_BURST_MAX_DURATION_S = 0.55
SWIPE_BURST_MIN_PEAK_V = 0.015

# Cooldown between commands
COMMAND_COOLDOWN_S = 1.25

# Point hold: frames the index finger must be held up/down before first trigger
POINT_HOLD_FRAMES = 18
# Point repeat: once triggered, fire again every N frames while still held
POINT_REPEAT_INTERVAL = 45

# Volume step per point trigger (percentage points, signed by direction)
VOLUME_STEP = 3

# Crossfade
CROSSFADE_MS = 450
CROSSFADE_TARGET_VOLUME_DROP = 35  # percentage points (max)

# Staff voice announcements (Vosk)
VOSK_MODEL_PATH = ""  # set to a local Vosk model folder path (e.g. "models/vosk-model-small-en-us-0.15")
VOICE_SAMPLE_RATE = 16000
VOICE_BLOCK_SIZE = 4000
STAFF_ANNOUNCEMENT_PHRASES = [
    "everyone listen up for a sec",
    "everyone listen up",
]
ANNOUNCEMENT_END_SILENCE_S = 1.7

# Event log
EVENT_LOG_MAX = 250


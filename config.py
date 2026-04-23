import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Spotify credentials (populated from .env)
# ---------------------------------------------------------------------------
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# ---------------------------------------------------------------------------
# Playlist IDs – replace these with real Spotify playlist IDs
# ---------------------------------------------------------------------------
PERSONAL_PLAYLIST = "4i0lx0ZRyMZWWBDgedWy9c?si=4299d7a96ab34c58&pt=d2868ae74d5799f0e9a1e97cc1f46361"  # Personal mode playlist
STAFF_PLAYLIST    = "7B1tUsr6cwRpSAlqa8BoTy?si=41dd9e829bd141d8"  # Staff mode playlist

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

# Cooldown between commands
COMMAND_COOLDOWN_S = 1.25

# Point hold: frames the index finger must be held up/down before first trigger
POINT_HOLD_FRAMES = 18
# Point repeat: once triggered, fire again every N frames while still held
POINT_REPEAT_INTERVAL = 45

# Volume step per point trigger (percentage points, signed by direction)
VOLUME_STEP = 5

# Crossfade
CROSSFADE_MS = 450
CROSSFADE_TARGET_VOLUME_DROP = 35  # percentage points (max)

# Dynamic theming – audio_features thresholds and timing
THEME_POLL_INTERVAL_S = 5       # how often the background thread checks for a new track
THEME_ENERGY_THRESHOLD = 0.6    # energy above this = "high energy" quadrant
THEME_VALENCE_THRESHOLD = 0.6   # valence above this = "high valence" quadrant
THEME_UPDATE_INTERVAL_S = 5.0   # how often CameraView refreshes the border colour

# Event log
EVENT_LOG_MAX = 250

# ---------------------------------------------------------------------------
# Vibe background + segmentation (Dynamic Theming replacement)
# ---------------------------------------------------------------------------
# Background blur strength (bigger = blurrier).
VIBE_BG_BLUR_SIGMA = 55.0

# Segmentation edge smoothing blur sigma.
SEG_EDGE_BLUR_SIGMA = 6.0

# Temporal smoothing factor for segmentation alpha (EMA). Higher = more responsive,
# lower = steadier edges.
SEG_TEMPORAL_SMOOTH_ALPHA = 0.35

# Album art fetch caching (seconds).
ALBUM_ART_CACHE_S = 12.0


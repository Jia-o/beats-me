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

# Personal mode: choose from multiple playlists (cycle with a macro)
PERSONAL_PLAYLISTS = [
    "37i9dQZF1EIfjzgnbx4yqL",
    "37i9dQZF1EIgG2NEOhqsD7",
]

# Staff mode: always play from this playlist
STAFF_PLAYLIST = "37i9dQZF1EIfjzgnbx4yqL"

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# ---------------------------------------------------------------------------
# Hands – gesture thresholds + standby/active gating
# ---------------------------------------------------------------------------
# Pinch: normalized Euclidean distance between thumb tip and index tip
PINCH_THRESHOLD = 0.05
# Pinch hold: consecutive frames the pinch must be held before firing
PINCH_HOLD_FRAMES = 4

# Swipe: track wrist x over this many frames; fire if total displacement exceeds threshold
# AND peak single-frame velocity exceeds SWIPE_MIN_VELOCITY (prevents slow drift from firing)
SWIPE_FRAMES = 10
SWIPE_THRESHOLD = 0.18          # Minimum normalized horizontal displacement
SWIPE_MIN_VELOCITY = 0.035      # Minimum single-frame delta to qualify as a deliberate swipe

# Standby/Active gating
WAVE_ARM_DURATION_S = 1.5
ACTIVE_WINDOW_S = 5.0
COMMAND_COOLDOWN_S = 1.25

# Swipe (v2): centroid burst detection (normalized by palm scale)
SWIPE_BURST_MIN_DISPLACEMENT = 0.35
SWIPE_BURST_MAX_DURATION_S = 0.55
SWIPE_BURST_MIN_PEAK_V = 0.015

# Point hold: frames the index finger must be held up/down before first trigger
POINT_HOLD_FRAMES = 18
# Point repeat: once triggered, fire again every N frames while still held
POINT_REPEAT_INTERVAL = 45

# Volume step per point trigger (percentage points, signed by direction)
VOLUME_STEP = 3

# Presence gating (personal mode auto-pause)
PRESENCE_GONE_TIMEOUT_S = 1.0
PRESENCE_DEBOUNCE_S = 0.75

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
STAFF_ANNOUNCEMENT_SAFE_VOLUME = 35

# Humor suggestions (UI queue)
HUMOR_SUGGESTIONS_ENABLED = True
HUMOR_SUGGESTION_REFRESH_S = 15.0
HUMOR_SUGGESTION_QUEUE_MAX = 5
HUMOR_TOPIC_SONGS = {
    "recursion": [
        "The Song That Never Ends",
        "Again (Lenny Kravitz)",
        "Repeat After Me",
    ],
    "sorting": [
        "Alphabet Song",
        "In the End",
        "Order Order",
    ],
    "javascript": [
        "Toxic",
        "Oops!... I Did It Again",
        "Why'd You Only Call Me When You're High?",
    ],
}
HUMOR_FALLBACK_SONGS = [
    "Under Pressure",
    "Work",
    "The Final Countdown",
]

# Event log
EVENT_LOG_MAX = 250

# ---------------------------------------------------------------------------
# Focus Mode – pose thresholds
# ---------------------------------------------------------------------------
# Head down: nose-to-shoulder offset below this ratio (normalized coords)
HEAD_DOWN_RATIO = 0.15
# Gone: frames without a detected pose before switching to "gone"
GONE_TIMEOUT = 90
# Posture stable: consecutive frames the same posture must be held before emitting
POSTURE_STABLE_FRAMES = 10


"""
config.py – API credentials, camera settings, and gesture/mode constants.

Playlist IDs below are placeholders. Replace with real Spotify playlist IDs.
Find a playlist ID by right-clicking it in Spotify → Share → Copy link;
the ID is the string after /playlist/ and before any '?'.
"""

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
PLAYLIST_FOCUS = "YOUR_FOCUS_PLAYLIST_ID"        # Focus Mode: head down / studying
PLAYLIST_ENERGIZE = "YOUR_ENERGIZE_PLAYLIST_ID"  # Focus Mode: upright / energized
PLAYLIST_MOODY = "YOUR_MOODY_PLAYLIST_ID"        # Emotion Mode: sad
PLAYLIST_UPBEAT = "YOUR_UPBEAT_PLAYLIST_ID"      # Emotion Mode: happy

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
GONE_TIMEOUT = 30

# ---------------------------------------------------------------------------
# Emotion Mode – face mesh thresholds
# ---------------------------------------------------------------------------
# Smile/frown: mouth-corner elevation relative to lip center (normalized coords)
SMILE_THRESHOLD = 0.008

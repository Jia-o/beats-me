"""
perception/_models.py – on-demand model file download helper.

MediaPipe Tasks API requires model bundle files (.task) that are not bundled
with the Python package.  This module downloads them from Google's public CDN
the first time they are needed and caches them in a top-level ``models/``
directory so subsequent starts are instant.
"""

import os
import urllib.request

# Directory where model files are cached (sibling of the project root
# relative to this file's location).
_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

# Public download URL for the hand landmarker model bundle.
HAND_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


def ensure_model(url: str, filename: str) -> str:
    """Return the absolute path to *filename*, downloading it first if absent.

    Parameters
    ----------
    url:
        Public URL to download the model bundle from.
    filename:
        Base name of the file to store locally (e.g. ``"hand_landmarker.task"``).

    Returns
    -------
    str
        Absolute path to the (now guaranteed to exist) model file.

    Raises
    ------
    RuntimeError
        If the model file does not exist and the download fails.
    """
    os.makedirs(_MODELS_DIR, exist_ok=True)
    path = os.path.abspath(os.path.join(_MODELS_DIR, filename))
    if not os.path.exists(path):
        print(f"[beats-me] Downloading {filename} …")
        tmp_path = path + ".tmp"
        try:
            urllib.request.urlretrieve(url, tmp_path)
            os.replace(tmp_path, path)
        except Exception as exc:
            # Clean up any partial download before raising.
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise RuntimeError(
                f"Failed to download MediaPipe model '{filename}' from {url}.\n"
                f"Check your internet connection and try again.\n"
                f"Original error: {exc}"
            ) from exc
        print(f"[beats-me] {filename} saved to {path}")
    return path

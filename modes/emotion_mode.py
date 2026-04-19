"""
modes/emotion_mode.py – maps detected facial emotion to Spotify playlists.

Emotion → Action mapping
------------------------
happy   → play PLAYLIST_UPBEAT
sad     → play PLAYLIST_MOODY
neutral → no action (avoid switching mid-song on transient expressions)
"""

import config


class EmotionMode:
    def __init__(self, controller):
        self._ctrl = controller
        self._last_emotion: str | None = None

    def handle(self, emotion: str | None):
        if emotion is None or emotion == self._last_emotion:
            return

        self._last_emotion = emotion

        if emotion == "happy":
            self._ctrl.play_playlist(config.PLAYLIST_UPBEAT)
        elif emotion == "sad":
            self._ctrl.play_playlist(config.PLAYLIST_MOODY)
        # neutral: leave current playback unchanged

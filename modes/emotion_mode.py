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

        if emotion == "happy":
            self._last_emotion = emotion
            self._ctrl.play_playlist(config.PLAYLIST_UPBEAT)
        elif emotion == "sad":
            self._last_emotion = emotion
            self._ctrl.play_playlist(config.PLAYLIST_MOODY)
        # neutral: leave current playback unchanged and don't update _last_emotion
        # so that a transient neutral read doesn't reset state and cause a
        # restart when the detected emotion returns to the previous value.

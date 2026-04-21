"""
modes/focus_mode.py – maps body posture to Spotify playlist / playback state.

Posture → Action mapping
------------------------
head_down → play PLAYLIST_FOCUS   (focused / studying)
upright   → play PLAYLIST_ENERGIZE (alert / energised)
gone      → pause playback
None      → no action (detection briefly lost, keep current state)
"""

import config


class FocusMode:
    def __init__(self, controller):
        self._ctrl = controller
        self._last_posture: str | None = None
        self._active_playlist: str | None = None

    def handle(self, posture: str | None):
        # None means detection was just lost – don't change anything yet
        if posture is None or posture == self._last_posture:
            return

        prev_posture = self._last_posture
        self._last_posture = posture

        if posture == "head_down":
            if self._active_playlist != config.PLAYLIST_FOCUS:
                self._active_playlist = config.PLAYLIST_FOCUS
                self._ctrl.play_playlist(config.PLAYLIST_FOCUS)
        elif posture == "upright":
            if self._active_playlist != config.PLAYLIST_ENERGIZE:
                self._active_playlist = config.PLAYLIST_ENERGIZE
                self._ctrl.play_playlist(config.PLAYLIST_ENERGIZE)
        elif posture == "gone":
            # Only pause if the person was upright (not mid-focus with head down),
            # to avoid pausing when pose detection briefly loses a bowed head.
            if prev_posture != "head_down":
                self._ctrl.pause()

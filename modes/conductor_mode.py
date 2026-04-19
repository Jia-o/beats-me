"""
modes/conductor_mode.py – maps hand gestures to Spotify playback controls.

Gesture → Action mapping
-------------------------
pinch        → toggle play/pause
swipe_left   → previous track
swipe_right  → next track
point_up     → volume up (VOLUME_STEP %)
point_down   → volume down (VOLUME_STEP %)
"""

import config


class ConductorMode:
    def __init__(self, controller):
        self._ctrl = controller

    def handle(self, gesture: str | None):
        if gesture is None:
            return

        if gesture == "pinch":
            self._ctrl.toggle_play()
        elif gesture == "swipe_left":
            self._ctrl.previous_track()
        elif gesture == "swipe_right":
            self._ctrl.next_track()
        elif gesture == "point_up":
            self._ctrl.adjust_volume(config.VOLUME_STEP)
        elif gesture == "point_down":
            self._ctrl.adjust_volume(-config.VOLUME_STEP)

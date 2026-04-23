import time

import config


class StaffMode:
    """
    Staff mode:
    - Plays from the staff playlist.
    - Gesture controls: pinch (pause/play), V-shape (skip), point (volume).
    - Shush gesture (index finger over lips) mutes Spotify while active.
    """

    def __init__(self, controller):
        self._ctrl = controller
        self._event_log: list[dict] = []
        self._last_command: str | None = None

        self._mute_active = False
        self._pre_mute_volume: int | None = None

        if config.STAFF_PLAYLIST:
            self._ctrl.play_playlist(config.STAFF_PLAYLIST)

    # ---------------------------- public hooks ----------------------------

    def close(self):
        # Ensure we never leave Spotify muted when exiting the mode.
        try:
            if self._mute_active:
                self._mute_active = False
                if hasattr(self._ctrl, "gesture_mute_release"):
                    self._ctrl.gesture_mute_release()
                elif self._pre_mute_volume is not None:
                    self._ctrl.set_volume(self._pre_mute_volume)
        except Exception:
            pass

    def get_status(self) -> dict:
        return {
            "mode": "staff",
            "mute_active": self._mute_active,
            "playlist": config.STAFF_PLAYLIST,
            "last_command": self._last_command,
        }

    def get_event_log(self) -> list[dict]:
        return list(self._event_log)

    def get_theme_color(self) -> tuple | None:
        if hasattr(self._ctrl, "get_theme_color"):
            return self._ctrl.get_theme_color()
        return None

    def handle_result(self, result: dict):
        command = result.get("command")
        if command:
            self._last_command = command
            self._log("command", {"command": command})
            self._handle_command(command)

        if result.get("shush_tap"):
            if not self._mute_active:
                self._mute_active = True
                self._log("mute_start", {"reason": "shush_tap"})
                if hasattr(self._ctrl, "gesture_mute_start"):
                    self._ctrl.gesture_mute_start()
                else:
                    # Fallback path: save volume (if possible) then mute.
                    if hasattr(self._ctrl, "get_current_volume"):
                        try:
                            self._pre_mute_volume = self._ctrl.get_current_volume()
                        except Exception:
                            self._pre_mute_volume = None
                    self._ctrl.set_volume(0)
            else:
                self._mute_active = False
                self._log("mute_release", {"reason": "shush_tap"})
                if hasattr(self._ctrl, "gesture_mute_release"):
                    self._ctrl.gesture_mute_release()
                elif self._pre_mute_volume is not None:
                    self._ctrl.set_volume(self._pre_mute_volume)

    # ---------------------------- internals ----------------------------

    def _handle_command(self, command: str):
        if command == "toggle_play":
            self._ctrl.toggle_play()
        elif command == "next":
            self._ctrl.next_track_crossfade()
        elif command == "prev":
            self._ctrl.previous_track_crossfade()
        elif command == "vol_up":
            self._ctrl.adjust_volume(config.VOLUME_STEP)
        elif command == "vol_down":
            self._ctrl.adjust_volume(-config.VOLUME_STEP)

    def _log(self, event: str, data: dict):
        self._event_log.append({"ts": time.time(), "event": event, **data})
        if len(self._event_log) > config.EVENT_LOG_MAX:
            del self._event_log[: len(self._event_log) - config.EVENT_LOG_MAX]


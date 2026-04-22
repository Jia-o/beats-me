import time

import config


class PersonalMode:
    """
    Personal mode:
    - Plays from one of many personal playlists (user can cycle).
    - Gesture controls (via HandsEngine command output).
    - Auto-pauses when the user is out of frame (hand not detected) and resumes on return.
    """

    def __init__(self, controller):
        self._ctrl = controller
        self._playlist_idx = 0

        self._last_hand_seen_ts: float | None = None
        self._presence_paused = False
        self._last_presence_change_ts = 0.0

        self._event_log: list[dict] = []
        self._last_command: str | None = None

        # Play immediately on entry so the mode "does something"
        if config.PERSONAL_PLAYLISTS:
            self._ctrl.play_playlist(config.PERSONAL_PLAYLISTS[self._playlist_idx])

    # ---------------------------- public hooks ----------------------------

    def close(self):
        # Nothing to stop for PersonalMode yet; exists for symmetry with StaffMode.
        return

    def get_status(self) -> dict:
        return {
            "mode": "personal",
            "gesture_state": None,  # provided by HandsEngine in CameraView status merge
            "presence_auto_pause": True,
            "presence_paused": self._presence_paused,
            "playlist": self._current_playlist_id(),
            "last_command": self._last_command,
        }

    def get_event_log(self) -> list[dict]:
        return list(self._event_log)

    # CameraView will prefer this richer handler if present
    def handle_result(self, result: dict):
        now = time.time()

        hand_present = bool(result.get("hand_present"))
        command = result.get("command")

        # ---- presence gate (auto-pause/resume) ----
        if hand_present:
            self._last_hand_seen_ts = now
            if self._presence_paused and (now - self._last_presence_change_ts) >= config.PRESENCE_DEBOUNCE_S:
                self._presence_paused = False
                self._last_presence_change_ts = now
                self._log("presence_resume", {})
                self._ctrl.toggle_play()
        else:
            # Only consider "gone" after a timeout to avoid flapping on brief drops
            if self._last_hand_seen_ts is not None and (now - self._last_hand_seen_ts) >= config.PRESENCE_GONE_TIMEOUT_S:
                if not self._presence_paused and (now - self._last_presence_change_ts) >= config.PRESENCE_DEBOUNCE_S:
                    self._presence_paused = True
                    self._last_presence_change_ts = now
                    self._log("presence_pause", {})
                    self._ctrl.pause()

        # ---- commands (already gated by HandsEngine standby/active) ----
        if command:
            self._last_command = command
            self._log("command", {"command": command})
            self._handle_command(command)

    # ---------------------------- internals ----------------------------

    def _current_playlist_id(self) -> str | None:
        if not config.PERSONAL_PLAYLISTS:
            return None
        return config.PERSONAL_PLAYLISTS[self._playlist_idx]

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
        elif command == "cycle_playlist":
            self._playlist_idx = (self._playlist_idx + 1) % max(1, len(config.PERSONAL_PLAYLISTS))
            pl = self._current_playlist_id()
            if pl:
                self._ctrl.play_playlist(pl)
        else:
            # Unknown command; ignore
            return

    def _log(self, event: str, data: dict):
        self._event_log.append({"ts": time.time(), "event": event, **data})
        if len(self._event_log) > config.EVENT_LOG_MAX:
            del self._event_log[: len(self._event_log) - config.EVENT_LOG_MAX]

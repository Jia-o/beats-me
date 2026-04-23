import time

import config


class StaffMode:
    """
    Staff mode:
    - Plays from the staff playlist.
    - Gesture controls: pinch (pause/play), V-shape (skip), point (volume).
    """

    def __init__(self, controller):
        self._ctrl = controller
        self._event_log: list[dict] = []
        self._last_command: str | None = None
        self._command_seq: int = 0
        self._is_playing: bool | None = None

        self._play_counts: dict[str, int] = {}
        self._track_titles: dict[str, str] = {}
        self._last_track_id: str | None = None
        self._running = True

        if config.STAFF_PLAYLIST:
            self._ctrl.play_playlist(config.STAFF_PLAYLIST)

        # Background poller to track "most played" while staff playlist is running.
        # Best-effort: if the controller can't provide track info, this stays empty.
        import threading
        threading.Thread(target=self._track_poll_loop, daemon=True).start()

    # ---------------------------- public hooks ----------------------------

    def close(self):
        self._running = False
        return

    def get_status(self) -> dict:
        is_playing = None
        if hasattr(self._ctrl, "is_music_playing"):
            try:
                is_playing = bool(self._ctrl.is_music_playing())
            except Exception:
                is_playing = None
        self._is_playing = is_playing
        return {
            "mode": "staff",
            "playlist": config.STAFF_PLAYLIST,
            "last_command": self._last_command,
            "command_seq": self._command_seq,
            "is_playing": self._is_playing,
        }

    def get_event_log(self) -> list[dict]:
        return list(self._event_log)

    def get_leaderboard(self, limit: int = 5) -> list[tuple[str, int]]:
        items = sorted(self._play_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        out: list[tuple[str, int]] = []
        n = max(0, int(limit))
        for track_id, count in items[:n]:
            title = self._track_titles.get(track_id) or track_id
            out.append((title, int(count)))
        return out

    def get_theme_color(self) -> tuple | None:
        if hasattr(self._ctrl, "get_theme_color"):
            return self._ctrl.get_theme_color()
        return None

    def handle_result(self, result: dict):
        command = result.get("command")
        if command:
            self._last_command = command
            self._command_seq += 1
            self._log("command", {"command": command})
            self._handle_command(command)

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

    def _track_poll_loop(self):
        while self._running:
            try:
                if hasattr(self._ctrl, "get_current_track_info"):
                    info = self._ctrl.get_current_track_info()
                else:
                    info = None

                if info and info.get("id") and info.get("name"):
                    track_id = info["id"]
                    if track_id != self._last_track_id:
                        self._last_track_id = track_id
                        title = info["name"]
                        artists = info.get("artists") or ""
                        if artists:
                            title = f"{title} — {artists}"
                        self._track_titles[track_id] = title
                        self._play_counts[track_id] = int(self._play_counts.get(track_id, 0)) + 1
                        self._log("track", {"track_id": track_id, "title": title})
            except Exception:
                pass
            time.sleep(2.0)

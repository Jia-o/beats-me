import time

import config
from voice.announcement_listener import AnnouncementListener


class StaffMode:
    """
    Staff mode:
    - Plays from the staff playlist.
    - Gesture controls: pinch (pause/play), swipe (skip), point (volume).
    - Voice phrase pauses music for announcements, resumes when speech settles.
    """

    def __init__(self, controller):
        self._ctrl = controller
        self._event_log: list[dict] = []
        self._last_command: str | None = None

        self._announcement_paused = False

        if config.STAFF_PLAYLIST:
            self._ctrl.play_playlist(config.STAFF_PLAYLIST)

        self._listener = AnnouncementListener(
            phrases=config.STAFF_ANNOUNCEMENT_PHRASES,
            on_announcement_start=self._on_announcement_start,
            on_announcement_end=self._on_announcement_end,
        )
        self._listener.start()

    # ---------------------------- public hooks ----------------------------

    def close(self):
        try:
            self._listener.stop()
        except Exception:
            pass

    def get_status(self) -> dict:
        return {
            "mode": "staff",
            "announcement_paused": self._announcement_paused,
            "playlist": config.STAFF_PLAYLIST,
            "last_command": self._last_command,
        }

    def get_event_log(self) -> list[dict]:
        return list(self._event_log)

    def handle_result(self, result: dict):
        command = result.get("command")
        if command:
            self._last_command = command
            self._log("command", {"command": command})
            self._handle_command(command)

    # ---------------------------- voice events ----------------------------

    def _on_announcement_start(self, meta: dict):
        if not self._announcement_paused:
            self._announcement_paused = True
            self._log("announcement_pause", meta)
            self._ctrl.pause()

    def _on_announcement_end(self, meta: dict):
        if self._announcement_paused:
            self._announcement_paused = False
            self._log("announcement_resume", meta)
            self._ctrl.toggle_play()

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


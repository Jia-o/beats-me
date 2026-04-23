import time

import config


class PersonalMode:
    """
    Personal mode:
    - Plays from the personal playlist.
    - Gesture controls: pinch (pause/play), swipe (skip), point (volume).
    """

    def __init__(self, controller):
        self._ctrl = controller
        self._event_log: list[dict] = []
        self._last_command: str | None = None

        if config.PERSONAL_PLAYLIST:
            self._ctrl.play_playlist(config.PERSONAL_PLAYLIST)

    # ---------------------------- public hooks ----------------------------

    def close(self):
        return

    def get_status(self) -> dict:
        return {
            "mode": "personal",
            "playlist": config.PERSONAL_PLAYLIST,
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


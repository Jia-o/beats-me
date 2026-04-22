import threading
import time

import config
from voice.announcement_listener import AnnouncementListener
from humor.suggester import HumorSuggestionQueue


class StaffMode:
    """
    Staff mode:
    - Always plays from the staff playlist.
    - Gesture controls (via HandsEngine command output).
    - Voice phrase pauses music for announcements, resumes when speech settles.
    - Does NOT auto-pause when no person is in frame.
    - Optional: topic-aware humorous song suggestions (queue UI only).
    """

    def __init__(self, controller):
        self._ctrl = controller
        self._event_log: list[dict] = []
        self._last_command: str | None = None

        self._announcement_paused = False
        self._last_announcement_ts = 0.0

        self._suggestions = HumorSuggestionQueue()

        # Start staff playlist immediately
        if config.STAFF_PLAYLIST:
            self._ctrl.play_playlist(config.STAFF_PLAYLIST)

        # Voice listener (best-effort; will self-disable if dependencies/model missing)
        self._listener = AnnouncementListener(
            phrases=config.STAFF_ANNOUNCEMENT_PHRASES,
            on_announcement_start=self._on_announcement_start,
            on_announcement_end=self._on_announcement_end,
        )
        self._listener.start()

        # Background: periodically refresh suggestions based on topic (if enabled)
        self._stop = False
        self._suggestion_thread = threading.Thread(target=self._suggestion_loop, daemon=True)
        self._suggestion_thread.start()

    # ---------------------------- public hooks ----------------------------

    def close(self):
        self._stop = True
        try:
            self._listener.stop()
        except Exception:
            pass

    def get_status(self) -> dict:
        return {
            "mode": "staff",
            "presence_auto_pause": False,
            "announcement_paused": self._announcement_paused,
            "playlist": config.STAFF_PLAYLIST,
            "last_command": self._last_command,
            "topic": self._suggestions.topic,
            "suggestions": self._suggestions.peek(3),
        }

    def get_event_log(self) -> list[dict]:
        return list(self._event_log)

    def set_topic(self, topic: str):
        self._suggestions.set_topic(topic)
        self._log("topic_set", {"topic": topic})

    def handle_result(self, result: dict):
        command = result.get("command")
        if command:
            self._last_command = command
            self._log("command", {"command": command})
            self._handle_command(command)

    # ---------------------------- voice events ----------------------------

    def _on_announcement_start(self, meta: dict):
        now = time.time()
        self._last_announcement_ts = now
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
        elif command == "announcement_safe_volume":
            # A macro: quickly set volume to a preset for announcements / grading room comfort.
            self._ctrl.set_volume(config.STAFF_ANNOUNCEMENT_SAFE_VOLUME)
        elif command == "suggestion_next":
            # Pop a suggestion (UI only; no Spotify playlist modification scope yet)
            s = self._suggestions.pop()
            if s:
                self._log("suggestion_popped", {"suggestion": s})
        else:
            return

    def _suggestion_loop(self):
        while not self._stop:
            try:
                if config.HUMOR_SUGGESTIONS_ENABLED:
                    self._suggestions.refresh()
            except Exception:
                # Never crash the mode on suggestions
                pass
            time.sleep(config.HUMOR_SUGGESTION_REFRESH_S)

    def _log(self, event: str, data: dict):
        self._event_log.append({"ts": time.time(), "event": event, **data})
        if len(self._event_log) > config.EVENT_LOG_MAX:
            del self._event_log[: len(self._event_log) - config.EVENT_LOG_MAX]

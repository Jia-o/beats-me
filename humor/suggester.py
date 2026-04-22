import time

import config


class HumorSuggestionQueue:
    """
    Topic-aware humorous song suggestions.

    This intentionally does NOT auto-modify Spotify playlists (would require extra scopes
    like playlist-modify-private/public). Instead, it maintains a small suggestion queue
    that the UI can display and the user can "pop" from.
    """

    def __init__(self):
        self.topic: str | None = None
        self._queue: list[str] = []
        self._last_refresh_ts = 0.0

    def set_topic(self, topic: str):
        self.topic = (topic or "").strip() or None
        self._queue.clear()
        self._last_refresh_ts = 0.0

    def peek(self, n: int) -> list[str]:
        return self._queue[: max(0, n)]

    def pop(self) -> str | None:
        if not self._queue:
            return None
        return self._queue.pop(0)

    def refresh(self):
        now = time.time()
        if (now - self._last_refresh_ts) < config.HUMOR_SUGGESTION_REFRESH_S:
            return
        self._last_refresh_ts = now

        if not self.topic:
            return

        suggestions = _suggest_for_topic(self.topic)
        # Keep queue small and stable: append only new items
        for s in suggestions:
            if s not in self._queue:
                self._queue.append(s)
        del self._queue[config.HUMOR_SUGGESTION_QUEUE_MAX :]


def _suggest_for_topic(topic: str) -> list[str]:
    t = topic.lower()
    for key, vals in config.HUMOR_TOPIC_SONGS.items():
        if key in t:
            return list(vals)[: config.HUMOR_SUGGESTION_QUEUE_MAX]
    # fallback: a couple of generic “work/grading/coding” jokes
    return list(config.HUMOR_FALLBACK_SONGS)[: config.HUMOR_SUGGESTION_QUEUE_MAX]

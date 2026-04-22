import threading
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

import config

_SCOPE = (
    "user-modify-playback-state "
    "user-read-playback-state"
)


class SpotifyController:
    def __init__(self):
        self._sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config.SPOTIPY_CLIENT_ID,
                client_secret=config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=config.SPOTIPY_REDIRECT_URI,
                scope=_SCOPE,
            )
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_exc(exc: SpotifyException):
        if "No active device" in str(exc):
            print("[Spotify] No active device found – open Spotify on any device first.")
        else:
            print(f"[Spotify] Error: {exc}")

    def _dispatch(self, fn, *args, **kwargs):
        """Run *fn* in a daemon thread; swallow SpotifyExceptions gracefully."""

        def _worker():
            try:
                fn(*args, **kwargs)
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_worker, daemon=True).start()

    def _current_volume(self) -> int | None:
        playback = self._sp.current_playback()
        if playback and playback.get("device") and playback["device"].get("volume_percent") is not None:
            return int(playback["device"]["volume_percent"])
        return None

    def _set_volume(self, vol: int):
        self._sp.volume(max(0, min(100, int(vol))))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def next_track(self):
        print("[Spotify] → Next track")
        self._dispatch(self._sp.next_track)

    def previous_track(self):
        print("[Spotify] ← Previous track")
        self._dispatch(self._sp.previous_track)

    def set_volume(self, vol: int):
        print(f"[Spotify] 🔊 Set volume: {vol}%")

        def _worker():
            try:
                self._set_volume(vol)
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_worker, daemon=True).start()

    def next_track_crossfade(self):
        print("[Spotify] → Next track (crossfade)")
        self._dispatch(self._crossfade_skip, direction="next")

    def previous_track_crossfade(self):
        print("[Spotify] ← Previous track (crossfade)")
        self._dispatch(self._crossfade_skip, direction="prev")

    def _crossfade_skip(self, direction: str):
        """
        Spotify doesn't expose true local crossfade via the Web API.
        We approximate by ramping device volume down, skipping, then ramping back up.
        """
        try:
            base = self._current_volume()
            if base is None:
                # No device info; just skip
                return self._sp.next_track() if direction == "next" else self._sp.previous_track()

            drop = min(config.CROSSFADE_TARGET_VOLUME_DROP, base)
            low = max(0, base - drop)
            steps = 6
            step_ms = max(30, int(config.CROSSFADE_MS / (2 * steps)))

            # fade down
            for i in range(steps):
                vol = int(base + (low - base) * ((i + 1) / steps))
                self._set_volume(vol)
                time.sleep(step_ms / 1000.0)

            # skip
            if direction == "next":
                self._sp.next_track()
            else:
                self._sp.previous_track()

            # fade up
            for i in range(steps):
                vol = int(low + (base - low) * ((i + 1) / steps))
                self._set_volume(vol)
                time.sleep(step_ms / 1000.0)
        except SpotifyException as exc:
            self._handle_exc(exc)

    def toggle_play(self):
        print("[Spotify] ⏯  Toggle play/pause")

        def _toggle():
            try:
                playback = self._sp.current_playback()
                if playback and playback.get("is_playing"):
                    self._sp.pause_playback()
                else:
                    self._sp.start_playback()
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_toggle, daemon=True).start()

    def pause(self):
        print("[Spotify] ⏸  Pause")

        def _pause():
            try:
                self._sp.pause_playback()
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_pause, daemon=True).start()

    def adjust_volume(self, delta: int):
        """Change volume by *delta* percentage points (positive = louder)."""
        print(f"[Spotify] 🔊 Volume {delta:+}%")

        def _set_vol():
            try:
                playback = self._sp.current_playback()
                if playback and playback.get("device"):
                    current = playback["device"]["volume_percent"]
                    new_vol = max(0, min(100, current + delta))
                    self._sp.volume(new_vol)
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_set_vol, daemon=True).start()

    def play_playlist(self, playlist_id: str):
        print(f"[Spotify] 🎵 Play playlist: {playlist_id}")
        self._dispatch(
            self._sp.start_playback,
            context_uri=f"spotify:playlist:{playlist_id}",
        )

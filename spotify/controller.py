import threading

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def next_track(self):
        print("[Spotify] → Next track")
        self._dispatch(self._sp.next_track)

    def previous_track(self):
        print("[Spotify] ← Previous track")
        self._dispatch(self._sp.previous_track)

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

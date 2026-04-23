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

        # Duck / smooth-recover state
        self._pre_duck_volume: int | None = None
        self._recover_token: int = 0

        # Mute (gesture) state
        self._pre_mute_volume: int | None = None
        self._mute_active: bool = False

        # Dynamic theme state
        self._theme_color: tuple[int, int, int] = (180, 180, 180)  # neutral gray BGR
        self._theme_lock = threading.Lock()
        self._last_track_id: str | None = None

        # Start background theme poller
        threading.Thread(target=self._theme_poll_loop, daemon=True).start()

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

    def get_current_volume(self) -> int | None:
        """Public accessor for current device volume, if available."""
        try:
            return self._current_volume()
        except Exception:
            return None

    def is_music_playing(self) -> bool:
        try:
            playback = self._sp.current_playback()
            return bool(playback and playback.get("is_playing"))
        except Exception:
            return False

    def get_album_art_url(self) -> str | None:
        """
        Return the best available album art URL for the currently playing track.
        """
        try:
            playback = self._sp.current_playback()
            if not playback or not playback.get("item"):
                return None
            album = playback["item"].get("album") or {}
            images = album.get("images") or []
            if not images:
                return None
            # Prefer highest-res (Spotify returns sorted by size desc).
            return images[0].get("url")
        except Exception:
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

    # ------------------------------------------------------------------
    # Volume ducking and smooth recovery
    # ------------------------------------------------------------------

    def duck_volume(self, target: int = config.DUCK_TARGET_VOLUME):
        """Save current volume and immediately drop to *target* percent."""
        print(f"[Spotify] Duck volume → {target}%")

        def _do_duck():
            try:
                vol = self._current_volume()
                if vol is not None:
                    self._pre_duck_volume = vol
                self._set_volume(target)
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_do_duck, daemon=True).start()

    def smooth_recover_volume(self):
        """Gradually restore volume to the level saved by duck_volume (3 s fade-in)."""
        target = self._pre_duck_volume
        if target is None:
            return
        print(f"[Spotify] Smooth volume recovery → {target}%")
        # Bump token to cancel any ongoing recovery thread.
        self._recover_token += 1
        token = self._recover_token
        self._dispatch(self._do_smooth_recover, target, token)

    def _do_smooth_recover(self, target: int, token: int):
        try:
            current = self._current_volume()
            if current is None:
                return
            vol = current
            while vol < target:
                if self._recover_token != token:
                    return  # cancelled by a newer call
                vol = min(vol + config.SMOOTH_RECOVER_STEP, target)
                self._set_volume(vol)
                time.sleep(config.SMOOTH_RECOVER_INTERVAL_S)
        except SpotifyException as exc:
            self._handle_exc(exc)

    # ------------------------------------------------------------------
    # Gesture mute (shush)
    # ------------------------------------------------------------------

    def gesture_mute_start(self):
        """Save current volume and set Spotify volume to 0."""
        if self._mute_active:
            return
        self._mute_active = True

        def _do():
            try:
                vol = self._current_volume()
                if vol is not None and vol > 0:
                    self._pre_mute_volume = vol
                self._set_volume(0)
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_do, daemon=True).start()

    def gesture_mute_release(self):
        """Restore volume to the value saved by gesture_mute_start (if any)."""
        if not self._mute_active:
            return
        self._mute_active = False
        target = self._pre_mute_volume
        if target is None:
            return

        def _do():
            try:
                self._set_volume(target)
            except SpotifyException as exc:
                self._handle_exc(exc)

        threading.Thread(target=_do, daemon=True).start()

    # ------------------------------------------------------------------
    # Dynamic theming
    # ------------------------------------------------------------------

    def get_theme_color(self) -> tuple[int, int, int]:
        """Return a cached BGR color derived from the current track's audio features."""
        with self._theme_lock:
            return self._theme_color

    def _theme_poll_loop(self):
        """Daemon thread: detect song changes and update the cached theme color."""
        while True:
            try:
                track_id = self._current_track_id()
                if track_id and track_id != self._last_track_id:
                    self._last_track_id = track_id
                    features = self._sp.audio_features([track_id])
                    if features and features[0]:
                        valence = features[0].get("valence", 0.5)
                        energy = features[0].get("energy", 0.5)
                        color = self._map_to_color(valence, energy)
                        with self._theme_lock:
                            self._theme_color = color
            except Exception:
                pass
            time.sleep(config.THEME_POLL_INTERVAL_S)

    def _current_track_id(self) -> str | None:
        try:
            playback = self._sp.current_playback()
            if playback and playback.get("item"):
                return playback["item"].get("id")
        except Exception:
            pass
        return None

    @staticmethod
    def _map_to_color(valence: float, energy: float) -> tuple[int, int, int]:
        """Map Spotify audio features valence/energy to a BGR color.

        Quadrant mapping:
          High energy + High valence  →  Warm Orange  (bright / party)
          High energy + Low  valence  →  Bright Red   (intense / dark)
          Low  energy + High valence  →  Sun Yellow   (peaceful / happy)
          Low  energy + Low  valence  →  Deep Blue    (calm / melancholy)
        """
        if energy >= config.THEME_ENERGY_THRESHOLD and valence >= config.THEME_VALENCE_THRESHOLD:
            return (0, 165, 255)    # Orange (BGR)
        if energy >= config.THEME_ENERGY_THRESHOLD and valence < config.THEME_VALENCE_THRESHOLD:
            return (0, 30, 220)     # Red (BGR)
        if energy < config.THEME_ENERGY_THRESHOLD and valence >= config.THEME_VALENCE_THRESHOLD:
            return (0, 230, 255)    # Yellow (BGR)
        return (160, 80, 30)        # Deep Blue (BGR)

"""
spotify/mock_controller.py – drop-in replacement for SpotifyController that
prints every action to the console instead of hitting the Spotify API.

Useful for testing the vision/gesture logic without valid credentials or an
active Spotify device.

Usage in main.py (or anywhere):
    from spotify.mock_controller import MockSpotifyController as SpotifyController
"""


class MockSpotifyController:
    def next_track(self):
        print("[Mock] → Next track")

    def previous_track(self):
        print("[Mock] ← Previous track")

    def next_track_crossfade(self):
        print("[Mock] → Next track (crossfade)")

    def previous_track_crossfade(self):
        print("[Mock] ← Previous track (crossfade)")

    def toggle_play(self):
        print("[Mock] ⏯  Toggle play/pause")

    def pause(self):
        print("[Mock] ⏸  Pause")

    def set_volume(self, vol: int):
        print(f"[Mock] 🔊 Set volume: {vol}%")

    def adjust_volume(self, delta: int):
        print(f"[Mock] 🔊 Volume {delta:+}%")

    def play_playlist(self, playlist_id: str):
        print(f"[Mock] 🎵 Play playlist: {playlist_id}")

    def duck_volume(self, target: int = 15):
        print(f"[Mock] Duck volume → {target}%")

    def smooth_recover_volume(self):
        print("[Mock] Smooth volume recovery")

    def get_theme_color(self) -> tuple:
        return (180, 180, 180)  # neutral gray BGR

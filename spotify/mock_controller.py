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

    def toggle_play(self):
        print("[Mock] ⏯  Toggle play/pause")

    def pause(self):
        print("[Mock] ⏸  Pause")

    def adjust_volume(self, delta: int):
        print(f"[Mock] 🔊 Volume {delta:+}%")

    def play_playlist(self, playlist_id: str):
        print(f"[Mock] 🎵 Play playlist: {playlist_id}")

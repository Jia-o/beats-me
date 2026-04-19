"""
main.py – beats-me entry point and global state manager.

Flow
----
1. Initialise the SpotifyController (triggers OAuth browser flow on first run).
2. Show SelectionScreen (the Tk root window) and enter the main event loop.
3. When the user picks a mode the selection screen hides itself, the
   appropriate engine + mode handler are created, and a CameraView
   (CTkToplevel) is opened.
4. Pressing M (or closing CameraView) destroys the camera window and
   brings the selection screen back – no restart required.

Fallback
--------
If Spotify credentials are missing or authentication fails the app falls
back to MockSpotifyController, which prints actions to the console so the
vision logic can still be exercised.
"""

import customtkinter as ctk

import config
from perception.hands import HandsEngine
from perception.pose  import PoseEngine
from perception.face  import FaceEngine
from modes.conductor_mode import ConductorMode
from modes.focus_mode     import FocusMode
from modes.emotion_mode   import EmotionMode
from ui.selection_screen  import SelectionScreen
from ui.camera_view       import CameraView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _build_controller():
    """Return a real or mock Spotify controller depending on credential availability."""
    if not all([config.SPOTIPY_CLIENT_ID, config.SPOTIPY_CLIENT_SECRET]):
        print(
            "[beats-me] Spotify credentials not found in .env – "
            "running with MockSpotifyController (actions printed to console)."
        )
        from spotify.mock_controller import MockSpotifyController
        return MockSpotifyController()

    try:
        from spotify.controller import SpotifyController
        return SpotifyController()
    except Exception as exc:  # noqa: BLE001
        print(f"[beats-me] Spotify auth failed ({exc}) – falling back to mock controller.")
        from spotify.mock_controller import MockSpotifyController
        return MockSpotifyController()


def main():
    controller = _build_controller()
    root = None  # assigned below; referenced by closures

    def on_back():
        root.deiconify()

    def on_mode_selected(mode: str):
        root.withdraw()  # hide selection screen; keep Tk root alive

        if mode == "conductor":
            engine  = HandsEngine()
            handler = ConductorMode(controller)
            name    = "Conductor Mode"
        elif mode == "focus":
            engine  = PoseEngine()
            handler = FocusMode(controller)
            name    = "Focus Mode"
        elif mode == "emotion":
            engine  = FaceEngine()
            handler = EmotionMode(controller)
            name    = "Emotion Mode"
        else:
            root.deiconify()
            return

        CameraView(
            master=root,
            mode_name=name,
            engine=engine,
            mode_handler=handler,
            on_back=on_back,
        )

    root = SelectionScreen(on_mode_selected=on_mode_selected)
    root.mainloop()


if __name__ == "__main__":
    main()

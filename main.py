import customtkinter as ctk

import config
from perception.hands import HandsEngine
from modes.personal_mode import PersonalMode
from modes.staff_mode    import StaffMode
from ui.selection_screen  import SelectionScreen
from ui.camera_view       import CameraView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _build_controller():
    """Return a real or mock Spotify controller depending on credential availability."""
    if not all([config.SPOTIPY_CLIENT_ID, config.SPOTIPY_CLIENT_SECRET,
                config.SPOTIPY_REDIRECT_URI]):
        print(
            "[beats-me] Spotify credentials not found in .env – "
            "running with MockSpotifyController (actions printed to console)."
        )
        from spotify.mock_controller import MockSpotifyController
        return MockSpotifyController()

    try:
        from spotify.controller import SpotifyController
        return SpotifyController()
    except Exception as exc:
        print(f"[beats-me] Spotify auth failed ({exc}) – falling back to mock controller.")
        from spotify.mock_controller import MockSpotifyController
        return MockSpotifyController()


def main():
    controller = _build_controller()
    root = None  # assigned below; referenced by closures

    def on_back():
        controller.pause()
        root.deiconify()

    def on_mode_selected(mode: str):
        root.withdraw()  # hide selection screen; keep Tk root alive

        if mode == "personal":
            engine = HandsEngine()
            handler = PersonalMode(controller)
            name = "Personal Mode"
        elif mode == "staff":
            engine = HandsEngine()
            handler = StaffMode(controller)
            name = "Staff Mode"
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

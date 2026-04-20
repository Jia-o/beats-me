"""
ui/selection_screen.py – splash / mode-picker window (the Tk root window).

Pressing M while on this screen is a no-op (already here).
"""

import customtkinter as ctk

_MODES = [
    (
        "🎵  Conductor Mode",
        "conductor",
        "Control playback with hand gestures",
    ),
    (
        "📚  Focus Mode",
        "focus",
        "Playlist adapts to your posture",
    ),
    (
        "😊  Emotion Mode",
        "emotion",
        "Playlist adapts to your mood",
    ),
]


class SelectionScreen(ctk.CTk):
    """
    Parameters
    ----------
    on_mode_selected : callable
        Called with a mode string ("conductor" | "focus" | "emotion") when
        the user clicks one of the mode buttons.
    """

    def __init__(self, on_mode_selected):
        super().__init__()
        self._callback = on_mode_selected

        self.title("beats-me")
        self.geometry("500x420")
        self.resizable(False, False)

        self._build_ui()

        # M / m on the selection screen: already here – no-op
        self.bind("<KeyPress-m>", lambda _e: None)
        self.bind("<KeyPress-M>", lambda _e: None)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="beats-me",
            font=ctk.CTkFont(size=40, weight="bold"),
        )
        title.grid(row=0, column=0, pady=(44, 6))

        subtitle = ctk.CTkLabel(
            self,
            text="Choose your control mode",
            font=ctk.CTkFont(size=14),
            text_color="gray70",
        )
        subtitle.grid(row=1, column=0, pady=(0, 28))

        for i, (label, mode, desc) in enumerate(_MODES):
            card = ctk.CTkFrame(self, corner_radius=10)
            card.grid(row=i + 2, column=0, padx=48, pady=7, sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            btn = ctk.CTkButton(
                card,
                text=label,
                width=190,
                height=38,
                command=lambda m=mode: self._callback(m),
            )
            btn.grid(row=0, column=0, padx=12, pady=12)

            ctk.CTkLabel(
                card,
                text=desc,
                anchor="w",
                text_color="gray70",
            ).grid(row=0, column=1, padx=(0, 12), pady=12, sticky="w")

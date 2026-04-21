"""
ui/selection_screen.py – splash / mode-picker window (the Tk root window).

Pressing M while on this screen is a no-op (already here).
"""

import customtkinter as ctk

_MODES = [
    (
        "🎵",
        "Conductor Mode",
        "conductor",
        "Control playback with hand gestures\nPinch · Swipe · Point",
    ),
    (
        "📚",
        "Focus Mode",
        "focus",
        "Playlist adapts to your posture\nHead down → focus  ·  Upright → energize",
    ),
]

_ACCENT   = "#1DB954"   # Spotify-ish green kept as on-theme accent
_BG_CARD  = "#1e1e2e"
_BG_HOVER = "#2a2a3e"


class SelectionScreen(ctk.CTk):
    """
    Parameters
    ----------
    on_mode_selected : callable
        Called with a mode string ("conductor" | "focus") when the user
        clicks one of the mode buttons.
    """

    def __init__(self, on_mode_selected):
        super().__init__()
        self._callback = on_mode_selected

        self.title("beats-me")
        self.geometry("660x520")
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

        # ---- header ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, pady=(52, 4))

        ctk.CTkLabel(
            header,
            text="beats-me",
            font=ctk.CTkFont(family="Helvetica", size=52, weight="bold"),
            text_color=_ACCENT,
        ).pack()

        ctk.CTkLabel(
            header,
            text="Choose how you want to control your music",
            font=ctk.CTkFont(size=15),
            text_color="gray60",
        ).pack(pady=(6, 0))

        # ---- mode cards ----
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=1, column=0, padx=48, pady=(28, 0), sticky="ew")
        cards_frame.grid_columnconfigure(0, weight=1)

        for i, (icon, label, mode, desc) in enumerate(_MODES):
            card = ctk.CTkFrame(cards_frame, corner_radius=14, fg_color=_BG_CARD)
            card.grid(row=i, column=0, pady=10, sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            # icon badge
            icon_lbl = ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=34),
                width=60,
            )
            icon_lbl.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=20)

            # title + description
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=18, weight="bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="sw", pady=(18, 2))

            ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color="gray60",
                anchor="w",
                justify="left",
            ).grid(row=1, column=1, sticky="nw", pady=(0, 18))

            # launch button
            btn = ctk.CTkButton(
                card,
                text="Select",
                width=90,
                height=36,
                corner_radius=8,
                fg_color=_ACCENT,
                hover_color="#17a845",
                text_color="#000000",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda m=mode: self._callback(m),
            )
            btn.grid(row=0, column=2, rowspan=2, padx=20, pady=20)

        # ---- footer hint ----
        ctk.CTkLabel(
            self,
            text="Press  M  at any time to return here",
            font=ctk.CTkFont(size=12),
            text_color="gray40",
        ).grid(row=2, column=0, pady=(18, 0))

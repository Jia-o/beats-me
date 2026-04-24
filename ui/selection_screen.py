import customtkinter as ctk

_MODES = [
    (
        "💚",
        "Personal Mode",
        "personal",
        "My playlists :)",
    ),
    (
        "💙",
        "Staff Mode",
        "staff",
        "Grading playlist :)",
    ),
]

_ACCENT      = "#B8C9A9" # Soft Sage Green
_BG_MAIN     = "#FDF6F0" # Warm Cream
_BG_CARD     = "#FFFFFF" # Pure White
_TEXT_MAIN   = "#5D5D5D" # Soft Charcoal
_TEXT_DIM    = "#A0A0A0" # Light Gray
_BTN_HOVER   = "#A4B595"


class SelectionScreen(ctk.CTk):
    def __init__(self, on_mode_selected):
        super().__init__()
        self._callback = on_mode_selected

        self.title("beats-me")
        self.geometry("1040x720")
        self.configure(fg_color=_BG_MAIN)

        # self._build_background()
        self._build_ui()
        self._add_floating_decor("🌸", 0.8, 0.2)
        self._add_floating_decor("🌼", 0.1, 0.15,)
        self._add_floating_decor("✏️", 0.88, 0.1)
        self._add_floating_decor("🌸", 0.08, 0.8)
        self._add_floating_decor("🌼", 0.94, 0.5)
        self._add_floating_decor("✏️", 0.15, 0.9)

    # def _build_background(self):
    #     self.canvas = ctk.CTkCanvas(
    #         self, 
    #         width=1040, 
    #         height=720, 
    #         bg=_BG_MAIN, 
    #         highlightthickness=0
    #     )
    #     self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

    #     decorations = [
    #                 ("🌸", 0.1, 0.15, 40), ("🌸", 0.88, 0.1, 35),
    #                 ("✏️", 0.08, 0.8, 45), ("✏️", 0.94, 0.5, 40),
    #                 ("🌼", 0.85, 0.85, 50), ("🌷", 0.15, 0.9, 30)
    #             ]
                
    #     for icon, rx, ry, sz in decorations:
    #         self.canvas.create_text(
    #             0, 0, # Placeholder, repositioned by anchor
    #             text=icon, 
    #             font=("Arial", sz), 
    #             fill="gray", # Not used for emojis but good practice
    #             tags="bg_decor"
    #         )
    #         # Use relative placement
    #         self.canvas.move(self.canvas.find_all()[-1], 1040*rx, 720*ry)
    #         self.canvas.tk.call('lower', self.canvas._w)

    def _build_ui(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.grid(row=0, column=0, pady=(0, 40))

        ctk.CTkLabel(
            header,
            text="beats-me",
            font=ctk.CTkFont(family="Helvetica", size=72, weight="bold"),
            text_color=_ACCENT,
        ).pack()

        ctk.CTkLabel(
            header,
            text="control spotify music and data with hand gestures",
            font=ctk.CTkFont(size=20, slant="italic"),
            text_color=_TEXT_DIM,
        ).pack()

        # ---- Mode Cards Container ----
        cards_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="n")

        for i, (icon, label, mode, desc) in enumerate(_MODES):
            # The Card
            card = ctk.CTkFrame(
                cards_frame, 
                corner_radius=25, 
                fg_color=_BG_CARD,
                border_width=2,
                border_color="#E8E8E8",
                width=700,
                height=160
            )
            card.grid(row=i, column=0, pady=15)
            card.grid_propagate(False) # Keeps card size fixed for better alignment

            # 1. Icon (Left)
            icon_lbl = ctk.CTkLabel(card, text=icon, font=("Arial", 50))
            icon_lbl.place(relx=0.1, rely=0.5, anchor="center")

            # 2. Text Content (Centered horizontally in the middle section)
            # By using place with relx=0.45, we ensure it's always centered regardless of length
            text_container = ctk.CTkFrame(card, fg_color="transparent")
            text_container.place(relx=0.45, rely=0.5, anchor="center")

            ctk.CTkLabel(
                text_container,
                text=label,
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color=_TEXT_MAIN
            ).pack(anchor="w")

            ctk.CTkLabel(
                text_container,
                text=desc,
                font=ctk.CTkFont(size=16),
                text_color=_TEXT_DIM
            ).pack(anchor="w")

            # 3. Launch Button (Right)
            btn = ctk.CTkButton(
                card,
                text="Select",
                width=140,
                height=50,
                corner_radius=25, # Rounded "Pill" shape
                fg_color=_ACCENT,
                hover_color=_BTN_HOVER,
                text_color="#FFFFFF",
                font=ctk.CTkFont(size=16, weight="bold"),
                command=lambda m=mode: self._callback(m),
            )
            btn.place(relx=0.85, rely=0.5, anchor="center")

        # ---- Footer Hint ----
        ctk.CTkLabel(
            self.main_container,
            text="Press  M  to return home",
            font=ctk.CTkFont(size=14),
            text_color=_TEXT_DIM,
        ).grid(row=2, column=0, pady=(30, 0))

    def _add_floating_decor(self, icon, rx, ry):
            lbl = ctk.CTkLabel(self, text=icon, font=("Arial", 40), fg_color="transparent")
            lbl.place(relx=rx, rely=ry, anchor="center")
            lbl.lift()
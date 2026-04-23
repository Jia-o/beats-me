import queue
import threading
import time

import cv2
import customtkinter as ctk
from PIL import Image

import config
import re 

# ---------------------------------------------------------------------------
# HUD overlay label tables  (BGR colours for cv2.putText)
# ---------------------------------------------------------------------------

_COMMAND_LABELS: dict[str, tuple[str, tuple[int, int, int]]] = {
    "toggle_play": ("Play / Pause",  (100, 255, 100)),
    "next":        ("Next Track >>", (255, 200, 100)),
    "prev":        ("<< Prev Track", (255, 200, 100)),
    "vol_up":      ("Volume Up",     (80,  255, 180)),
    "vol_down":    ("Volume Down",   (80,  180, 255)),
}

_PENDING_LABELS: dict[str, tuple[str, tuple[int, int, int]]] = {
    "toggle_play": ("Pinch...",           (180, 255, 180)),
    "vol_up":      ("Raising volume...",  (100, 255, 200)),
    "vol_down":    ("Lowering volume...", (100, 200, 255)),
    "v_shape":     ("V-shape...",         (200, 200, 100)),
}

_HAND_DETECTED_LABEL = ("Hand detected", (200, 200, 200))
_NO_OVERLAY = ("", (0, 0, 0))  # returned when there is nothing to display


class CameraView(ctk.CTkToplevel):
    DISPLAY_W = 960
    DISPLAY_H = 540

    def __init__(self, master, mode_name: str, engine, mode_handler, on_back):
        super().__init__(master)

        self.title(f"beats-me  –  {mode_name}")
        self.geometry(f"{self.DISPLAY_W}x{self.DISPLAY_H + 56}")
        self.resizable(False, False)

        self._engine = engine
        self._handler = mode_handler
        self._on_back = on_back

        self._frame_q: queue.Queue = queue.Queue(maxsize=2)
        self._running = False
        self._latest_result: dict = {}
        self._debug_win = None
        self._debug_text = None
        self._log_win = None
        self._log_text = None

        # Dynamic theme: border colour updated from controller audio_features.
        # Stored as a BGR tuple; written only from the Tk main thread.
        self._theme_color: tuple[int, int, int] = (180, 180, 180)
        self._last_theme_update: float = 0.0
        self._flash_text: str = ""
        self._flash_until: float = 0.0
        self._last_flash_command_seq: int | None = None

        self._build_ui()

        # Pressing M from the camera view returns to selection
        self.bind("<KeyPress-m>", self._go_back)
        self.bind("<KeyPress-M>", self._go_back)
        self.bind("<KeyPress-d>", lambda _e: self._toggle_debug())
        self.bind("<KeyPress-D>", lambda _e: self._toggle_debug())
        self.bind("<KeyPress-l>", lambda _e: self._toggle_log())
        self.bind("<KeyPress-L>", lambda _e: self._toggle_log())
        self.protocol("WM_DELETE_WINDOW", self._go_back)

        # Give the window a moment to render before starting the camera
        self.after(120, self._start)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        self._video_label = ctk.CTkLabel(
            self,
            text="",
            width=self.DISPLAY_W,
            height=self.DISPLAY_H,
        )
        self._video_label.pack()

        bar = ctk.CTkFrame(self, height=56, corner_radius=0)
        bar.pack(fill="x")

        self._hint_label = ctk.CTkLabel(
            bar,
            text="Press  M  to return • D debug • L log",
            text_color="gray60",
        )
        self._hint_label.pack(pady=(10, 0))

        self._status_label = ctk.CTkLabel(
            bar,
            text="",
            text_color="gray70",
            font=ctk.CTkFont(size=12),
        )
        self._status_label.pack(pady=(0, 10))

    # ------------------------------------------------------------------
    # Camera thread
    # ------------------------------------------------------------------

    def _start(self):
        self._engine.start()
        self._running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        self._poll_frame()

    def _capture_loop(self):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAPTURE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAPTURE_HEIGHT)

        if not cap.isOpened():
            print(f"[ERROR] Camera index {config.CAMERA_INDEX} not found.")
            self._running = False
            return

        try:
            while self._running:
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                annotated, result = self._engine.process_frame(frame)
                self._latest_result = result

                # Prefer rich result handler if available; keep backward compatibility
                if hasattr(self._handler, "handle_result"):
                    self._handler.handle_result(result)
                else:
                    action_key = result.get("gesture") or result.get("posture") or result.get("emotion")
                    if action_key:
                        self._handler.handle(action_key)

                display = cv2.resize(annotated, (self.DISPLAY_W, self.DISPLAY_H))

                # -- Helper for Outlined Text (Define this inside the loop or as a method) --
                def draw_outlined(img, text, pos, scale, color, thick):
                    # Draw Black Outline
                    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thick + 2, cv2.LINE_AA)
                    # Draw Main Color Text
                    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)

                # ── Visual Feedback Overlay ──────────────────────────────────
                overlay_text, overlay_color = self._get_overlay_info(self._latest_result)
                if overlay_text:
                    draw_outlined(display, overlay_text, (12, 38), 1.0, overlay_color, 2)

                # ── State-change flash (REDUCED FONT SIZE) ───────────────────
                if time.time() < self._flash_until and self._flash_text:
                    # Reduced from 1.6 to 1.0
                    draw_outlined(display, self._flash_text, (18, 92), 1.0, (255, 255, 255), 2)

                # ── Staff leaderboard overlay (REPOSITIONED & FILTERED) ──────
                if hasattr(self._handler, "get_leaderboard"):
                    try:
                        lb = self._handler.get_leaderboard(limit=5) or []
                        if lb:
                            # Move X further left (from -440 to -320) to stay on screen
                            x = self.DISPLAY_W - 320 
                            y = 40
                            draw_outlined(display, "Top Played This Session:", (x, y), 0.6, (180, 180, 180), 2)
                            
                            y += 30

                            for idx, (raw_title, count) in enumerate(lb, start=1):
                                parts = re.split(r'\W{2,}', raw_title)
                                song = parts[0].strip()
                                artist = parts[1].strip() if len(parts) > 1 else "Unknown"
                                display_song = f"{idx}. {song[:22]}.." if len(song) > 22 else f"{idx}. {song}"
                                draw_outlined(display, display_song, (x, y), 0.6, (255, 255, 255), 2)

                                y += 22
                                display_artist = artist[:22] + ".." if len(artist) > 22 else artist
                                draw_outlined(display, f"   {display_artist}", (x, y), 0.45, (180, 180, 180), 1)
                                y += 35
                    except Exception:
                        pass

                # ── Dynamic Theme Border ──────────────────────────────────────
                h, w = display.shape[:2]
                cv2.rectangle(display, (0, 0), (w - 1, h - 1), self._theme_color, 18)

                rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)

                if not self._frame_q.full():
                    self._frame_q.put(img)
                time.sleep(0.01)
        finally:
            cap.release()

    def _poll_frame(self):
        """Checks the queue for new frames and updates the UI label."""
        if not self._running:
            return

        try:
            img = self._frame_q.get_nowait()
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(self.DISPLAY_W, self.DISPLAY_H),
            )
            self._video_label.configure(image=ctk_img)
            self._video_label.image = ctk_img
        except queue.Empty:
            pass

        # Refresh theme colour from controller every THEME_UPDATE_INTERVAL_S seconds.
        now = time.time()
        if now - self._last_theme_update >= config.THEME_UPDATE_INTERVAL_S:
            self._last_theme_update = now
            self._refresh_theme_color()

        # Schedule next check in ~30ms (aiming for 30-60 FPS UI updates)
        self._update_status()
        self.after(30, self._poll_frame)

    def _refresh_theme_color(self):
        """Ask the mode handler for the latest theme color and cache it."""
        try:
            if hasattr(self._handler, "get_theme_color"):
                color = self._handler.get_theme_color()
                if color:
                    self._theme_color = color
        except Exception:
            pass

    def _get_overlay_info(self, result: dict) -> tuple[str, tuple[int, int, int]]:
        """Return (hud_text, bgr_color) for the frame overlay, or ('', ...) for none."""
        command = result.get("command")
        if command and command in _COMMAND_LABELS:
            return _COMMAND_LABELS[command]

        pending = (result.get("debug") or {}).get("pending")
        if pending and pending in _PENDING_LABELS:
            return _PENDING_LABELS[pending]

        if result.get("hand_present"):
            return _HAND_DETECTED_LABEL

        return _NO_OVERLAY

    def _update_status(self):
        try:
            status = {}
            if hasattr(self._engine, "get_status"):
                status.update(self._engine.get_status() or {})
            if hasattr(self._handler, "get_status"):
                status.update(self._handler.get_status() or {})

            parts = []
            if status.get("last_command"):
                parts.append(f"cmd: {status['last_command']}")
            if status.get("announcement_paused"):
                parts.append("announcement-paused")
            if status.get("is_playing") is True:
                parts.append("playing")
            elif status.get("is_playing") is False:
                parts.append("paused")

            self._status_label.configure(text=" | ".join(parts))
        except Exception:
            # Status is best-effort; never break the UI loop.
            return

        self._update_debug_windows()
        self._maybe_trigger_flash(status)

    def _maybe_trigger_flash(self, status: dict):
        try:
            last_cmd = status.get("last_command")
            if last_cmd != "toggle_play":
                return

            # Only flash once per command (not once per time window).
            seq = status.get("command_seq")
            if isinstance(seq, int) and self._last_flash_command_seq == seq:
                return
            self._flash_text = "PLAY / PAUSE TOGGLED"

            now = time.time()
            self._flash_until = now + 1.1
            if isinstance(seq, int):
                self._last_flash_command_seq = seq
        except Exception:
            return

    def _toggle_debug(self):
        if self._debug_win and self._debug_win.winfo_exists():
            self._debug_win.destroy()
            self._debug_win = None
            self._debug_text = None
            return

        win = ctk.CTkToplevel(self)
        win.title("beats-me – debug")
        win.geometry("560x520")
        win.resizable(True, True)
        txt = ctk.CTkTextbox(win)
        txt.pack(fill="both", expand=True)
        self._debug_win = win
        self._debug_text = txt
        self._update_debug_windows()

    def _toggle_log(self):
        if self._log_win and self._log_win.winfo_exists():
            self._log_win.destroy()
            self._log_win = None
            self._log_text = None
            return

        win = ctk.CTkToplevel(self)
        win.title("beats-me – event log")
        win.geometry("760x520")
        win.resizable(True, True)
        txt = ctk.CTkTextbox(win)
        txt.pack(fill="both", expand=True)
        self._log_win = win
        self._log_text = txt
        self._update_debug_windows()

    def _update_debug_windows(self):
        # Debug window
        if self._debug_text and self._debug_win and self._debug_win.winfo_exists():
            try:
                self._debug_text.delete("1.0", "end")
                self._debug_text.insert("end", "Latest engine result:\n")
                self._debug_text.insert("end", f"{self._latest_result}\n\n")
                if hasattr(self._handler, "get_status"):
                    self._debug_text.insert("end", "Handler status:\n")
                    self._debug_text.insert("end", f"{self._handler.get_status()}\n")
            except Exception:
                pass

        # Log window
        if self._log_text and self._log_win and self._log_win.winfo_exists():
            try:
                self._log_text.delete("1.0", "end")
                if hasattr(self._handler, "get_event_log"):
                    log = self._handler.get_event_log() or []
                    for item in log[-120:]:
                        self._log_text.insert("end", f"{item}\n")
                else:
                    self._log_text.insert("end", "No event log available for this mode.\n")
            except Exception:
                pass

    def _go_back(self, _event=None):
        self._running = False
        self._engine.stop()
        if hasattr(self._handler, "close"):
            try:
                self._handler.close()
            except Exception:
                pass
        self.destroy()
        self._on_back()
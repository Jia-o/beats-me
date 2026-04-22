"""
ui/camera_view.py – displays the live camera feed with MediaPipe overlays.

Architecture
------------
* A daemon thread captures frames from the webcam and runs the active
  perception engine.  Each processed frame is placed in a small queue.
* The Tkinter event loop polls that queue every ~33 ms (~30 fps) and updates
  a CTkLabel to show the latest frame.
* Spotify API calls are already dispatched to daemon threads by the controller,
  so the camera thread only calls mode_handler.handle(), which is fast.

Press M (or m) to stop the camera and return to the mode-selection screen.
"""

import queue
import threading
import time

import cv2
import customtkinter as ctk
from PIL import Image

import config


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

        self._build_ui()

        # Pressing M from the camera view returns to selection
        self.bind("<KeyPress-m>", self._go_back)
        self.bind("<KeyPress-M>", self._go_back)
        self.bind("<KeyPress-d>", lambda _e: self._toggle_debug())
        self.bind("<KeyPress-D>", lambda _e: self._toggle_debug())
        self.bind("<KeyPress-l>", lambda _e: self._toggle_log())
        self.bind("<KeyPress-L>", lambda _e: self._toggle_log())
        self.bind("<KeyPress-t>", lambda _e: self._set_topic())
        self.bind("<KeyPress-T>", lambda _e: self._set_topic())
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
            text="Press  M  to return • D debug • L log • T topic (staff)",
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

        # Schedule next check in ~30ms (aiming for 30-60 FPS UI updates)
        self._update_status()
        self.after(30, self._poll_frame)

    def _update_status(self):
        try:
            status = {}
            if hasattr(self._engine, "get_status"):
                status.update(self._engine.get_status() or {})
            if hasattr(self._handler, "get_status"):
                status.update(self._handler.get_status() or {})

            parts = []
            if status.get("gesture_state"):
                parts.append(f"hands: {status['gesture_state']}")
            if status.get("last_command"):
                parts.append(f"cmd: {status['last_command']}")
            if status.get("presence_paused"):
                parts.append("auto-paused")
            if status.get("announcement_paused"):
                parts.append("announcement-paused")
            if status.get("topic"):
                parts.append(f"topic: {status['topic']}")
            if status.get("suggestions"):
                s = status["suggestions"]
                if isinstance(s, list) and s:
                    parts.append("suggest: " + " · ".join(s[:2]))

            self._status_label.configure(text=" | ".join(parts))
        except Exception:
            # Status is best-effort; never break the UI loop.
            return

        self._update_debug_windows()

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

    def _set_topic(self):
        if not hasattr(self._handler, "set_topic"):
            return
        try:
            dlg = ctk.CTkInputDialog(text="Set grading topic (e.g. recursion):", title="Staff topic")
            val = (dlg.get_input() or "").strip()
            if val:
                self._handler.set_topic(val)
        except Exception:
            return

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
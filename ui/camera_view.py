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

import cv2
import customtkinter as ctk
from PIL import Image

import config


class CameraView(ctk.CTkToplevel):
    """
    Parameters
    ----------
    master       : CTk root window (SelectionScreen)
    mode_name    : human-readable mode label shown in the window title
    engine       : PerceptionEngine subclass (already instantiated, not yet started)
    mode_handler : ConductorMode / FocusMode / EmotionMode instance
    on_back      : callable – invoked when the user presses M or closes the window
    """

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

        self._build_ui()

        # Pressing M from the camera view returns to selection
        self.bind("<KeyPress-m>", self._go_back)
        self.bind("<KeyPress-M>", self._go_back)
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

        ctk.CTkLabel(
            bar,
            text="Press  M  to return to mode selection",
            text_color="gray60",
        ).pack(pady=16)

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

        while self._running:
            ok, frame = cap.read()
            if not ok:
                continue

            # Mirror so the feed feels natural (like a mirror / selfie view)
            frame = cv2.flip(frame, 1)

            annotated, result = self._engine.process_frame(frame)

            # Route result to the active mode handler
            gesture = result.get("gesture")
            posture = result.get("posture")
            emotion = result.get("emotion")
            if gesture is not None:
                self._handler.handle(gesture)
            elif posture is not None:
                self._handler.handle(posture)
            elif emotion is not None:
                self._handler.handle(emotion)

            # Resize to display dimensions and convert color space
            display = cv2.resize(annotated, (self.DISPLAY_W, self.DISPLAY_H))
            rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)

            if not self._frame_q.full():
                self._frame_q.put(img)

        cap.release()

    # ------------------------------------------------------------------
    # Tkinter polling loop (runs on the main thread)
    # ------------------------------------------------------------------

    def _poll_frame(self):
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
            self._video_label.image = ctk_img  # keep a reference to prevent GC
        except queue.Empty:
            pass

        self.after(33, self._poll_frame)  # ≈ 30 fps

    # ------------------------------------------------------------------
    # Back navigation
    # ------------------------------------------------------------------

    def _go_back(self, _event=None):
        self._running = False
        self._engine.stop()
        self.destroy()
        self._on_back()

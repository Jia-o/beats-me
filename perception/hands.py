"""
perception/hands.py – gesture recognition for Conductor Mode.

Gestures detected
-----------------
pinch       – thumb tip + index tip distance drops below threshold (toggle: fires
              once per close after PINCH_HOLD_FRAMES, resets when hand opens).
left        – wrist moves left  > SWIPE_THRESHOLD over SWIPE_FRAMES frames.
right       – wrist moves right > SWIPE_THRESHOLD over SWIPE_FRAMES frames.
up          – index finger extended upward, other fingers curled, held for
              POINT_HOLD_FRAMES then repeating every POINT_REPEAT_INTERVAL frames.
down        – same but finger angled downward.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
from collections import deque

from .engine import PerceptionEngine
from ._models import ensure_model, HAND_MODEL_URL
import config

_vision        = mp.tasks.vision
_BaseOptions   = mp.tasks.BaseOptions
_HandLandmarker        = _vision.HandLandmarker
_HandLandmarkerOptions = _vision.HandLandmarkerOptions
_HandLandmarksConn     = _vision.HandLandmarksConnections
_RunningMode           = _vision.RunningMode
_mp_drawing        = _vision.drawing_utils
_mp_drawing_styles = _vision.drawing_styles


class HandsEngine(PerceptionEngine):
    def __init__(self):
        super().__init__()
        self._landmarker = None

        # Raw motion history (for wave + swipe)
        self._centroid_hist: deque = deque(maxlen=60)  # (t, x, y, scale)
        self._wave_start_ts: float | None = None
        self._wave_last_sign: int | None = None
        self._wave_sign_changes = 0

        # Swipe latch (single-fire)
        self._swipe_active = False
        self._swipe_start_ts: float | None = None
        self._swipe_start_x: float | None = None
        self._swipe_peak_v = 0.0

        # Gesture gating state machine
        self._state: str = "standby"  # standby | active | cooldown
        self._state_until_ts: float = 0.0
        self._cooldown_until_ts: float = 0.0
        self._last_command: str | None = None

        # Pinch state
        self._pinched = False
        self._pinch_frames = 0

        # Point hold counters
        self._point_up_frames = 0
        self._point_down_frames = 0

    def _reset_gesture_state(self):
        self._centroid_hist.clear()
        self._wave_start_ts = None
        self._wave_last_sign = None
        self._wave_sign_changes = 0
        self._swipe_active = False
        self._swipe_start_ts = None
        self._swipe_start_x = None
        self._swipe_peak_v = 0.0

        self._state = "standby"
        self._state_until_ts = 0.0
        self._cooldown_until_ts = 0.0
        self._last_command = None

        self._pinched = False
        self._pinch_frames = 0
        self._point_up_frames = 0
        self._point_down_frames = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_start(self):
        model_path = ensure_model(HAND_MODEL_URL, "hand_landmarker.task")
        options = _HandLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=model_path),
            running_mode=_RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = _HandLandmarker.create_from_options(options)
        self._reset_gesture_state()

    def _on_stop(self):
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        result = {
            "hand_present": False,
            "gesture_state": self._state,
            "gesture": None,   # backward compat: mapped from command
            "command": None,   # canonical output
            "debug": {},
        }
        if not self._active or self._landmarker is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection = self._landmarker.detect(mp_image)

        annotated = frame.copy()

        if not detection.hand_landmarks:
            # Reset all stateful counters when hand leaves frame
            self._reset_gesture_state()
            return annotated, result

        # Use first detected hand only
        landmarks = detection.hand_landmarks[0]
        result["hand_present"] = True
        _mp_drawing.draw_landmarks(
            annotated,
            landmarks,
            _HandLandmarksConn.HAND_CONNECTIONS,
            _mp_drawing_styles.get_default_hand_landmarks_style(),
            _mp_drawing_styles.get_default_hand_connections_style(),
        )

        now = time.time()
        raw = self._classify_raw(landmarks)
        command = self._gate_and_map(now, raw)

        result["gesture_state"] = self._state
        result["command"] = command
        result["gesture"] = command  # legacy
        result["debug"] = {
            "raw": raw,
            "state": self._state,
            "cooldown_until": self._cooldown_until_ts,
        }
        return annotated, result

    # ------------------------------------------------------------------
    # Gesture classification
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        return {
            "gesture_state": self._state,
            "last_command": self._last_command,
        }

    def _classify_raw(self, lms) -> dict:
        thumb_tip  = lms[4]
        index_tip  = lms[8]
        index_mcp  = lms[5]
        middle_tip = lms[12]
        ring_tip   = lms[16]
        pinky_tip  = lms[20]
        wrist      = lms[0]

        now = time.time()

        # Palm centroid (more stable than wrist drift) and scale for normalization
        palm_pts = [lms[i] for i in (0, 5, 9, 13, 17)]
        cx = float(sum(p.x for p in palm_pts) / len(palm_pts))
        cy = float(sum(p.y for p in palm_pts) / len(palm_pts))
        palm_w = float(np.hypot(lms[5].x - lms[17].x, lms[5].y - lms[17].y))
        scale = max(1e-4, palm_w)
        self._centroid_hist.append((now, cx, cy, scale))

        # ----------------------------------------------------------------
        # 1. Pinch – thumb tip ↔ index tip distance (toggle, with hold debounce)
        # ----------------------------------------------------------------
        pinch_dist = float(np.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y))
        is_pinching = pinch_dist < config.PINCH_THRESHOLD

        if is_pinching and not self._pinched:
            self._pinch_frames += 1
            if self._pinch_frames >= config.PINCH_HOLD_FRAMES:
                self._pinched = True
                self._pinch_frames = 0
                # Reset hold counters so a pinch mid-point-hold doesn't double-fire
                self._point_up_frames = 0
                self._point_down_frames = 0
                pinch = True
            else:
                pinch = False
        elif not is_pinching:
            self._pinched = False
            self._pinch_frames = 0
            pinch = False
        else:
            pinch = False

        swipe = self._detect_swipe_burst()

        # ----------------------------------------------------------------
        # 3. Point up / down – only index finger extended, others curled
        #
        #    Point UP:   index tip well above wrist, tip above its MCP,
        #                other tips below their own MCPs (curled).
        #    Point DOWN: index tip well below wrist, tip below its MCP,
        #                other tips above the index tip (not extended down).
        # ----------------------------------------------------------------
        if not is_pinching:
            middle_mcp = lms[9]
            ring_mcp   = lms[13]
            pinky_mcp  = lms[17]

            # ---- pointing up ----
            index_above_mcp   = index_tip.y < index_mcp.y
            others_curled_up  = all(t.y > mcp.y
                                    for t, mcp in ((middle_tip, middle_mcp),
                                                   (ring_tip,   ring_mcp),
                                                   (pinky_tip,  pinky_mcp)))
            if index_above_mcp and others_curled_up and index_tip.y < wrist.y - 0.15:
                self._point_up_frames += 1
                self._point_down_frames = 0
            else:
                self._point_up_frames = 0

            # ---- pointing down ----
            index_below_mcp     = index_tip.y > index_mcp.y
            others_not_extended = all(t.y < index_tip.y + 0.05
                                      for t in (middle_tip, ring_tip, pinky_tip))
            if index_below_mcp and others_not_extended and index_tip.y > wrist.y + 0.08:
                self._point_down_frames += 1
                self._point_up_frames = 0
            else:
                self._point_down_frames = 0

        point_up = False
        point_down = False
        point_up_long = False
        if not is_pinching:
            if self._point_up_frames >= config.POINT_HOLD_FRAMES:
                elapsed = self._point_up_frames - config.POINT_HOLD_FRAMES
                if elapsed == 0 or elapsed % config.POINT_REPEAT_INTERVAL == 0:
                    point_up = True
                if self._point_up_frames >= (config.POINT_HOLD_FRAMES + 90):
                    point_up_long = True
            if self._point_down_frames >= config.POINT_HOLD_FRAMES:
                elapsed = self._point_down_frames - config.POINT_HOLD_FRAMES
                if elapsed == 0 or elapsed % config.POINT_REPEAT_INTERVAL == 0:
                    point_down = True

        wave = self._detect_wave()

        return {
            "pinch": pinch,
            "swipe": swipe,  # "left" | "right" | None
            "point_up": point_up,
            "point_down": point_down,
            "point_up_long": point_up_long,
            "wave": wave,
        }

    def _detect_wave(self) -> bool:
        """
        Wave: deliberate left-right oscillation for ~WAVE_ARM_DURATION_S.
        We look for multiple sign changes in the centroid x-velocity.
        """
        if len(self._centroid_hist) < 8:
            return False
        t2, x2, _, s2 = self._centroid_hist[-1]
        t1, x1, _, s1 = self._centroid_hist[-2]
        dt = max(1e-4, t2 - t1)
        v = (x2 - x1) / dt
        sign = 1 if v > 0 else (-1 if v < 0 else 0)
        amp = abs(x2 - x1) / max(s2, s1, 1e-4)

        if amp < 0.02:
            return False

        if self._wave_start_ts is None:
            self._wave_start_ts = t2
            self._wave_last_sign = sign if sign != 0 else None
            self._wave_sign_changes = 0
            return False

        if sign != 0 and self._wave_last_sign is not None and sign != self._wave_last_sign:
            self._wave_sign_changes += 1
            self._wave_last_sign = sign
        elif self._wave_last_sign is None and sign != 0:
            self._wave_last_sign = sign

        if (t2 - self._wave_start_ts) >= config.WAVE_ARM_DURATION_S:
            ok = self._wave_sign_changes >= 3
            self._wave_start_ts = None
            self._wave_last_sign = None
            self._wave_sign_changes = 0
            return bool(ok)
        return False

    def _detect_swipe_burst(self) -> str | None:
        if len(self._centroid_hist) < 6:
            return None
        t, x, _, s = self._centroid_hist[-1]

        # velocity (centroid x)
        t_prev, x_prev, _, s_prev = self._centroid_hist[-2]
        dt = max(1e-4, t - t_prev)
        vx = (x - x_prev) / dt
        self._swipe_peak_v = max(self._swipe_peak_v, abs(vx))

        if not self._swipe_active:
            # Start condition: a burst of motion
            if abs(vx) >= config.SWIPE_BURST_MIN_PEAK_V:
                self._swipe_active = True
                self._swipe_start_ts = t
                self._swipe_start_x = x
                self._swipe_peak_v = abs(vx)
            return None

        # Ongoing swipe: check duration + displacement
        if self._swipe_start_ts is None or self._swipe_start_x is None:
            self._swipe_active = False
            return None

        dur = t - self._swipe_start_ts
        dx = (x - self._swipe_start_x) / max(s, s_prev, 1e-4)

        if dur > config.SWIPE_BURST_MAX_DURATION_S:
            # time window expired; decide if it was a swipe
            fired = None
            if abs(dx) >= config.SWIPE_BURST_MIN_DISPLACEMENT and self._swipe_peak_v >= config.SWIPE_BURST_MIN_PEAK_V:
                fired = "right" if dx > 0 else "left"
            self._swipe_active = False
            self._swipe_start_ts = None
            self._swipe_start_x = None
            self._swipe_peak_v = 0.0
            return fired

        return None

    def _gate_and_map(self, now: float, raw: dict) -> str | None:
        """
        Standby -> Active is armed by a deliberate wave.
        In Active: accept one command, then Cooldown, then Standby.
        """
        # state expiry
        if self._state == "active" and now >= self._state_until_ts:
            self._state = "standby"
        if self._state == "cooldown" and now >= self._cooldown_until_ts:
            self._state = "standby"

        if self._state == "standby":
            if raw.get("wave"):
                self._state = "active"
                self._state_until_ts = now + config.ACTIVE_WINDOW_S
                return None
            return None

        if self._state == "active":
            cmd = None
            if raw.get("pinch"):
                cmd = "toggle_play"
            elif raw.get("swipe") == "right":
                cmd = "next"
            elif raw.get("swipe") == "left":
                cmd = "prev"
            elif raw.get("wave"):
                # Macro gesture: a second deliberate wave while active
                cmd = "cycle_playlist"
            elif raw.get("point_up_long"):
                cmd = "announcement_safe_volume"
            elif raw.get("point_up"):
                cmd = "vol_up"
            elif raw.get("point_down"):
                cmd = "vol_down"

            if cmd:
                self._last_command = cmd
                self._state = "cooldown"
                self._cooldown_until_ts = now + config.COMMAND_COOLDOWN_S
                return cmd
            return None

        # cooldown
        return None


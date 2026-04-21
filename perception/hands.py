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

        # Swipe: track wrist x positions across recent frames
        self._wrist_x_history: deque = deque(maxlen=config.SWIPE_FRAMES)

        # Pinch state
        self._pinched = False
        self._pinch_frames = 0

        # Point hold counters
        self._point_up_frames = 0
        self._point_down_frames = 0

    def _reset_gesture_state(self):
        self._wrist_x_history.clear()
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
        result = {"gesture": None}
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
        _mp_drawing.draw_landmarks(
            annotated,
            landmarks,
            _HandLandmarksConn.HAND_CONNECTIONS,
            _mp_drawing_styles.get_default_hand_landmarks_style(),
            _mp_drawing_styles.get_default_hand_connections_style(),
        )

        gesture = self._classify(landmarks)
        result["gesture"] = gesture
        return annotated, result

    # ------------------------------------------------------------------
    # Gesture classification
    # ------------------------------------------------------------------

    def _classify(self, lms) -> str | None:
        thumb_tip  = lms[4]
        index_tip  = lms[8]
        index_mcp  = lms[5]
        middle_tip = lms[12]
        ring_tip   = lms[16]
        pinky_tip  = lms[20]
        wrist      = lms[0]

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
                return "pinch"
        elif not is_pinching:
            self._pinched = False
            self._pinch_frames = 0

        # ----------------------------------------------------------------
        # 2. Swipe – horizontal wrist displacement over recent frames
        #    Requires BOTH total displacement AND a minimum peak per-frame
        #    velocity so that slow natural drift does not trigger a swipe.
        # ----------------------------------------------------------------
        self._wrist_x_history.append(wrist.x)
        if len(self._wrist_x_history) == config.SWIPE_FRAMES:
            dx = self._wrist_x_history[-1] - self._wrist_x_history[0]
            if abs(dx) > config.SWIPE_THRESHOLD:
                frames = self._wrist_x_history
                peak_vel = max(abs(frames[i + 1] - frames[i]) for i in range(len(frames) - 1))
                if peak_vel >= config.SWIPE_MIN_VELOCITY:
                    self._wrist_x_history.clear()
                    # In a mirrored frame: positive dx = hand moved toward screen-right
                    return "right" if dx > 0 else "left"

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

            # Fire on initial hold threshold, then every POINT_REPEAT_INTERVAL frames
            if self._point_up_frames >= config.POINT_HOLD_FRAMES:
                elapsed = self._point_up_frames - config.POINT_HOLD_FRAMES
                if elapsed == 0 or elapsed % config.POINT_REPEAT_INTERVAL == 0:
                    return "up"

            if self._point_down_frames >= config.POINT_HOLD_FRAMES:
                elapsed = self._point_down_frames - config.POINT_HOLD_FRAMES
                if elapsed == 0 or elapsed % config.POINT_REPEAT_INTERVAL == 0:
                    return "down"

        return None


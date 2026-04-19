"""
perception/hands.py – gesture recognition for Conductor Mode.

Gestures detected
-----------------
pinch       – thumb tip + index tip distance drops below threshold (toggle: fires
              once per close, resets when hand opens).
swipe_left  – wrist moves left  > SWIPE_THRESHOLD over SWIPE_FRAMES frames.
swipe_right – wrist moves right > SWIPE_THRESHOLD over SWIPE_FRAMES frames.
point_up    – index finger extended upward, other fingers curled, held for
              POINT_HOLD_FRAMES then repeating every POINT_REPEAT_INTERVAL frames.
point_down  – same but finger angled downward.
"""

import cv2
import mediapipe as mp
import numpy as np
from collections import deque

from .engine import PerceptionEngine
import config

_mp_hands = mp.solutions.hands
_mp_drawing = mp.solutions.drawing_utils


class HandsEngine(PerceptionEngine):
    def __init__(self):
        super().__init__()
        self._hands = None

        # Swipe: track wrist x positions across recent frames
        self._wrist_x_history: deque = deque(maxlen=config.SWIPE_FRAMES)

        # Pinch state
        self._pinched = False

        # Point hold counters
        self._point_up_frames = 0
        self._point_down_frames = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_start(self):
        self._hands = _mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self._wrist_x_history.clear()
        self._pinched = False
        self._point_up_frames = 0
        self._point_down_frames = 0

    def _on_stop(self):
        if self._hands:
            self._hands.close()
            self._hands = None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        result = {"gesture": None}
        if not self._active or self._hands is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        detection = self._hands.process(rgb)
        rgb.flags.writeable = True

        annotated = frame.copy()

        if not detection.multi_hand_landmarks:
            # Reset all stateful counters when hand leaves frame
            self._wrist_x_history.clear()
            self._pinched = False
            self._point_up_frames = 0
            self._point_down_frames = 0
            return annotated, result

        # Use first detected hand only
        hand_lm = detection.multi_hand_landmarks[0]
        _mp_drawing.draw_landmarks(annotated, hand_lm, _mp_hands.HAND_CONNECTIONS)

        gesture = self._classify(hand_lm)
        result["gesture"] = gesture
        return annotated, result

    # ------------------------------------------------------------------
    # Gesture classification
    # ------------------------------------------------------------------

    def _classify(self, lm) -> str | None:
        lms = lm.landmark

        thumb_tip  = lms[4]
        index_tip  = lms[8]
        index_pip  = lms[6]
        index_mcp  = lms[5]
        middle_tip = lms[12]
        ring_tip   = lms[16]
        pinky_tip  = lms[20]
        wrist      = lms[0]

        # ----------------------------------------------------------------
        # 1. Pinch – thumb tip ↔ index tip distance (toggle)
        # ----------------------------------------------------------------
        pinch_dist = float(np.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y))
        is_pinching = pinch_dist < config.PINCH_THRESHOLD

        if is_pinching and not self._pinched:
            self._pinched = True
            # Reset hold counters so a pinch mid-point-hold doesn't double-fire
            self._point_up_frames = 0
            self._point_down_frames = 0
            return "pinch"
        if not is_pinching:
            self._pinched = False

        # ----------------------------------------------------------------
        # 2. Swipe – horizontal wrist displacement over recent frames
        # ----------------------------------------------------------------
        self._wrist_x_history.append(wrist.x)
        if len(self._wrist_x_history) == config.SWIPE_FRAMES:
            dx = self._wrist_x_history[-1] - self._wrist_x_history[0]
            if abs(dx) > config.SWIPE_THRESHOLD:
                self._wrist_x_history.clear()
                # In a mirrored frame: positive dx = hand moved toward screen-right
                return "swipe_right" if dx > 0 else "swipe_left"

        # ----------------------------------------------------------------
        # 3. Point up / down – index extended, others curled, held
        # ----------------------------------------------------------------
        index_extended = index_tip.y < index_mcp.y  # tip above MCP (y smaller = higher)
        others_curled  = all(t.y > index_mcp.y for t in (middle_tip, ring_tip, pinky_tip))

        if index_extended and others_curled and not is_pinching:
            # Direction: compare index tip y to wrist y
            # tip well above wrist → pointing up; tip near or below → pointing down
            if index_tip.y < wrist.y - 0.15:
                self._point_up_frames += 1
                self._point_down_frames = 0
            elif index_tip.y > wrist.y + 0.05:
                self._point_down_frames += 1
                self._point_up_frames = 0
            else:
                self._point_up_frames = 0
                self._point_down_frames = 0

            # Fire on initial hold threshold, then every POINT_REPEAT_INTERVAL frames
            if self._point_up_frames >= config.POINT_HOLD_FRAMES:
                elapsed = self._point_up_frames - config.POINT_HOLD_FRAMES
                if elapsed == 0 or elapsed % config.POINT_REPEAT_INTERVAL == 0:
                    return "point_up"

            if self._point_down_frames >= config.POINT_HOLD_FRAMES:
                elapsed = self._point_down_frames - config.POINT_HOLD_FRAMES
                if elapsed == 0 or elapsed % config.POINT_REPEAT_INTERVAL == 0:
                    return "point_down"
        else:
            self._point_up_frames = 0
            self._point_down_frames = 0

        return None

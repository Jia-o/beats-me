"""
perception/pose.py – body posture detection for Focus Mode.

Postures detected
-----------------
upright    – nose is clearly above the shoulder midpoint (energised/alert).
head_down  – nose has dropped close to or below shoulder level (focused/reading).
gone       – no person detected for GONE_TIMEOUT consecutive frames.
None       – detection just lost; too early to call it "gone" yet (no action).
"""

import cv2
import mediapipe as mp

from .engine import PerceptionEngine
import config

_mp_pose = mp.solutions.pose
_mp_drawing = mp.solutions.drawing_utils
_mp_drawing_styles = mp.solutions.drawing_styles


class PoseEngine(PerceptionEngine):
    def __init__(self):
        super().__init__()
        self._pose = None
        self._gone_counter = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_start(self):
        self._pose = _mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._gone_counter = 0

    def _on_stop(self):
        if self._pose:
            self._pose.close()
            self._pose = None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        result = {"posture": None}
        if not self._active or self._pose is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        detection = self._pose.process(rgb)
        rgb.flags.writeable = True

        annotated = frame.copy()

        if detection.pose_landmarks:
            self._gone_counter = 0
            _mp_drawing.draw_landmarks(
                annotated,
                detection.pose_landmarks,
                _mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=_mp_drawing_styles.get_default_pose_landmarks_style(),
            )
            result["posture"] = self._classify(detection.pose_landmarks.landmark)
        else:
            self._gone_counter += 1
            if self._gone_counter >= config.GONE_TIMEOUT:
                result["posture"] = "gone"
            # else: result["posture"] stays None → FocusMode ignores it

        return annotated, result

    # ------------------------------------------------------------------
    # Posture classification
    # ------------------------------------------------------------------

    def _classify(self, landmarks) -> str:
        nose           = landmarks[_mp_pose.PoseLandmark.NOSE]
        left_shoulder  = landmarks[_mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[_mp_pose.PoseLandmark.RIGHT_SHOULDER]

        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2

        # In normalised coords y increases downward.
        # offset > 0  means nose is above shoulders (normal upright position).
        # offset < HEAD_DOWN_RATIO means nose has dropped toward shoulder level.
        offset = shoulder_mid_y - nose.y
        if offset < config.HEAD_DOWN_RATIO:
            return "head_down"
        return "upright"

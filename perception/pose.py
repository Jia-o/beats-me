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
from ._models import ensure_model, POSE_MODEL_URL
import config

_vision        = mp.tasks.vision
_BaseOptions   = mp.tasks.BaseOptions
_PoseLandmarker        = _vision.PoseLandmarker
_PoseLandmarkerOptions = _vision.PoseLandmarkerOptions
_PoseLandmarksConn     = _vision.PoseLandmarksConnections
_PoseLandmark          = _vision.PoseLandmark
_RunningMode           = _vision.RunningMode
_mp_drawing        = _vision.drawing_utils
_mp_drawing_styles = _vision.drawing_styles


class PoseEngine(PerceptionEngine):
    def __init__(self):
        super().__init__()
        self._landmarker = None
        self._gone_counter = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_start(self):
        model_path = ensure_model(POSE_MODEL_URL, "pose_landmarker_lite.task")
        options = _PoseLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=model_path),
            running_mode=_RunningMode.IMAGE,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = _PoseLandmarker.create_from_options(options)
        self._gone_counter = 0

    def _on_stop(self):
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        result = {"posture": None}
        if not self._active or self._landmarker is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection = self._landmarker.detect(mp_image)

        annotated = frame.copy()

        if detection.pose_landmarks:
            self._gone_counter = 0
            landmarks = detection.pose_landmarks[0]
            _mp_drawing.draw_landmarks(
                annotated,
                landmarks,
                _PoseLandmarksConn.POSE_LANDMARKS,
                _mp_drawing_styles.get_default_pose_landmarks_style(),
            )
            result["posture"] = self._classify(landmarks)
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
        nose           = landmarks[_PoseLandmark.NOSE]
        left_shoulder  = landmarks[_PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[_PoseLandmark.RIGHT_SHOULDER]

        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2

        # In normalised coords y increases downward.
        # offset > 0  means nose is above shoulders (normal upright position).
        # offset < HEAD_DOWN_RATIO means nose has dropped toward shoulder level.
        offset = shoulder_mid_y - nose.y
        if offset < config.HEAD_DOWN_RATIO:
            return "head_down"
        return "upright"


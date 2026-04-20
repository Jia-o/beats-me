"""
perception/face.py – facial emotion detection for Emotion Mode.

Uses MediaPipe Face Landmarker landmark positions to infer expression.

Emotions detected
-----------------
happy   – mouth corners are elevated relative to the lip centre (smile).
sad     – mouth corners are depressed relative to the lip centre (frown).
neutral – no strong expression detected.

Key Face Mesh landmarks used
----------------------------
  13  upper lip centre
  14  lower lip centre
  61  left  mouth corner
 291  right mouth corner
"""

import cv2
import mediapipe as mp

from .engine import PerceptionEngine
from ._models import ensure_model, FACE_MODEL_URL
import config

_vision        = mp.tasks.vision
_BaseOptions   = mp.tasks.BaseOptions
_FaceLandmarker        = _vision.FaceLandmarker
_FaceLandmarkerOptions = _vision.FaceLandmarkerOptions
_FaceLandmarksConn     = _vision.FaceLandmarksConnections
_RunningMode           = _vision.RunningMode
_mp_drawing        = _vision.drawing_utils
_mp_drawing_styles = _vision.drawing_styles

# Landmark indices – from the canonical MediaPipe Face Mesh 468-point map.
# Mouth corners (61, 291) and lip centre points (13, 14) are part of the
# outer lip contour; they show the most vertical movement during expressions.
_LEFT_CORNER  = 61
_RIGHT_CORNER = 291
_UPPER_LIP    = 13
_LOWER_LIP    = 14


class FaceEngine(PerceptionEngine):
    def __init__(self):
        super().__init__()
        self._face_landmarker = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_start(self):
        model_path = ensure_model(FACE_MODEL_URL, "face_landmarker.task")
        options = _FaceLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=model_path),
            running_mode=_RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._face_landmarker = _FaceLandmarker.create_from_options(options)

    def _on_stop(self):
        if self._face_landmarker:
            self._face_landmarker.close()
            self._face_landmarker = None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        result = {"emotion": "neutral"}
        if not self._active or self._face_landmarker is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection = self._face_landmarker.detect(mp_image)

        annotated = frame.copy()

        if detection.face_landmarks:
            landmarks = detection.face_landmarks[0]
            _mp_drawing.draw_landmarks(
                annotated,
                landmarks,
                _FaceLandmarksConn.FACE_LANDMARKS_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=_mp_drawing_styles.get_default_face_mesh_tesselation_style(),
            )
            result["emotion"] = self._classify(landmarks)

        return annotated, result

    # ------------------------------------------------------------------
    # Emotion classification
    # ------------------------------------------------------------------

    def _classify(self, landmarks) -> str:
        left_corner  = landmarks[_LEFT_CORNER]
        right_corner = landmarks[_RIGHT_CORNER]
        upper_lip    = landmarks[_UPPER_LIP]
        lower_lip    = landmarks[_LOWER_LIP]

        # Vertical midpoint of the mouth opening (y increases downward)
        mouth_center_y = (upper_lip.y + lower_lip.y) / 2
        # Average y of the two corners
        corner_avg_y   = (left_corner.y + right_corner.y) / 2

        # Positive diff  → corners are *above* mouth centre → smile
        # Negative diff  → corners are *below* mouth centre → frown
        diff = mouth_center_y - corner_avg_y

        if diff >  config.SMILE_THRESHOLD:
            return "happy"
        if diff < -config.SMILE_THRESHOLD:
            return "sad"
        return "neutral"


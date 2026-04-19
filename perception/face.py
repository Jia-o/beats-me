"""
perception/face.py – facial emotion detection for Emotion Mode.

Uses MediaPipe Face Mesh landmark positions to infer expression.

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
import config

_mp_face_mesh = mp.solutions.face_mesh
_mp_drawing = mp.solutions.drawing_utils
_mp_drawing_styles = mp.solutions.drawing_styles

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
        self._face_mesh = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_start(self):
        self._face_mesh = _mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def _on_stop(self):
        if self._face_mesh:
            self._face_mesh.close()
            self._face_mesh = None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        result = {"emotion": "neutral"}
        if not self._active or self._face_mesh is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        detection = self._face_mesh.process(rgb)
        rgb.flags.writeable = True

        annotated = frame.copy()

        if detection.multi_face_landmarks:
            face_lm = detection.multi_face_landmarks[0]
            _mp_drawing.draw_landmarks(
                annotated,
                face_lm,
                _mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=_mp_drawing_styles.get_default_face_mesh_tesselation_style(),
            )
            result["emotion"] = self._classify(face_lm.landmark)

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

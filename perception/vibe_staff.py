import cv2
import mediapipe as mp

import config
from ._models import ensure_model, FACE_MODEL_URL
from .vibe_hands import VibeHandsEngine

_vision = mp.tasks.vision
_BaseOptions = mp.tasks.BaseOptions
_RunningMode = _vision.RunningMode
_FaceLandmarker = _vision.FaceLandmarker
_FaceLandmarkerOptions = _vision.FaceLandmarkerOptions


class VibeStaffEngine(VibeHandsEngine):
    """
    Staff engine extends VibeHandsEngine:
    - Adds face landmarker to detect "shush" (index finger over lips).
    - Emits result['mute_active'] and leaves command gestures intact.
    """

    def __init__(self, background_provider=None):
        super().__init__(background_provider=background_provider)
        self.face_landmarker = None

    def _on_start(self):
        super()._on_start()
        face_model_path = ensure_model(FACE_MODEL_URL, "face_landmarker.task")
        face_options = _FaceLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=face_model_path),
            running_mode=_RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.face_landmarker = _FaceLandmarker.create_from_options(face_options)

    def _on_stop(self):
        if self.face_landmarker:
            self.face_landmarker.close()
            self.face_landmarker = None
        super()._on_stop()

    @staticmethod
    def _mouth_center(face_lms):
        """
        Use FaceMesh landmarks: 13 (upper lip) and 14 (lower lip).
        Return normalized (x, y) center.
        """
        try:
            up = face_lms[13]
            dn = face_lms[14]
            return ((up.x + dn.x) / 2.0, (up.y + dn.y) / 2.0)
        except Exception:
            return None

    def process_frame(self, frame):
        out, res = super().process_frame(frame)
        if not self._active or self.face_landmarker is None or self.hand_landmarker is None:
            return out, res

        if not res.get("hand_present"):
            res["mute_active"] = False
            return out, res

        # Face landmarks
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        face = self.face_landmarker.detect(mp_img)
        if not face.face_landmarks:
            res["mute_active"] = False
            return out, res

        mouth = self._mouth_center(face.face_landmarks[0])
        if not mouth:
            res["mute_active"] = False
            return out, res

        # Hand landmarks (index tip is landmark 8)
        hand = self.hand_landmarker.detect(mp_img)
        if not hand.hand_landmarks:
            res["mute_active"] = False
            return out, res

        idx_tip = hand.hand_landmarks[0][8]

        mx, my = mouth
        dx = abs(idx_tip.x - mx)
        dy = abs(idx_tip.y - my)

        shush = (dx <= config.SHUSH_MOUTH_X_THRESH) and (dy <= config.SHUSH_MOUTH_Y_THRESH)
        res["mute_active"] = bool(shush)
        return out, res


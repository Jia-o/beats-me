import cv2
import mediapipe as mp
import numpy as np
import time
from collections import deque

from .engine import PerceptionEngine
from ._models import ensure_model, HAND_MODEL_URL
import config

_vision                 = mp.tasks.vision
_BaseOptions            = mp.tasks.BaseOptions
_HandLandmarker         = _vision.HandLandmarker
_HandLandmarkerOptions  = _vision.HandLandmarkerOptions
_HandLandmarksConn      = _vision.HandLandmarksConnections
_RunningMode            = _vision.RunningMode
_mp_drawing             = _vision.drawing_utils
_mp_drawing_styles      = _vision.drawing_styles

class HandsEngine(PerceptionEngine):
    def __init__(self):
        super().__init__()
        self.landmarker = None

        # cooldown
        self.cooldown: float = 0.0
        self.prev: str | None = None

        # shapes
        self.vFrames = 0
        self.upFrames = 0
        self.downFrames = 0
        self.pinch = False

    def resetGestures(self):
        self.vFrames = 0
        self.upFrames = 0
        self.downFrames = 0
        self.pinch = False
        self.cooldown = 0.0
        self.prev = None

    def onStart(self):
        model_path = ensure_model(HAND_MODEL_URL, "hand_landmarker.task")
        options = _HandLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=model_path),
            running_mode=_RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = _HandLandmarker.create_from_options(options)
        self.resetGestures()

    def onStop(self):
        if self.landmarker:
            self.landmarker.close()
            self.landmarker = None

    def process_frame(self, frame):
        res = {"hand_present": False, "command": None}
        if not self._active or self.landmarker is None:
            return frame, res

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detect = self.landmarker.detect(mp_img)

        out = frame.copy()

        if not detect.hand_landmarks:
            self.resetGestures()
            return out, res

        lms = detect.hand_landmarks[0]
        res["hand_present"] = True
        
        _mp_drawing.draw_landmarks(
            out, lms, _HandLandmarksConn.HAND_CONNECTIONS,
            _mp_drawing_styles.get_default_hand_landmarks_style(),
            _mp_drawing_styles.get_default_hand_connections_style(),
        )

        now = time.time()
        raw = self.classify(lms)
        cmd = self._gate_and_map(now, raw)

        res["command"] = cmd
        return out, res

    def classify(self, lms) -> dict:
        thumbTip, indexTip, middleTip, ringTip, pinkyTip = lms[4], lms[8], lms[12], lms[16], lms[20]
        thumbMid, indexMid, middleMid, ringMid, pinkyMid = lms[5], lms[9], lms[13], lms[17]

        cx = sum(p.x for p in [lms[i] for i in (0, 5, 9, 13, 17)]) / 5

        # pinch 
        dist = np.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y)
        isPinching = dist < config.PINCH_THRESHOLD
        
        triggeredPinch = False
        if isPinching:
            if not self.pinch:
                triggeredPinch = True
                self.pinch = True
        else:
            self.pinch = False

        # v = index middle up + ring pinky down 
        idxUp, midUp = indexTip.y < indexMid.y - 0.05, middleTip.y < indexMid.y - 0.05
        rngDn, pnkDn = ringTip.y > ringMid.y, pinkyTip.y > pinkyMid.y
        
        vL, vR = False, False
        if idxUp and midUp and rngDn and pnkDn:
            self.vFrames += 1
            if self.vFrames >= config.POINT_HOLD_FRAMES:
                if cx < 0.4: vL = True
                elif cx > 0.6: vR = True
        else:
            self.vFrames = 0

        up, dn = False, False
        curled = all(t.y > m.y for t, m in [(middleTip, middleMid), (ringTip, ringMid), (pinkyTip, pinkyMid)])
        
        if not (idxUp and midUp): # skip if v-sign active
            if indexTip.y < indexMid.y - 0.1 and curled:
                self.upFrames += 1
                self.downFrames = 0
            elif indexTip.y > indexMid.y + 0.1 and curled:
                self.downFrames += 1
                self.upFrames = 0
            else:
                self.upFrames = self.downFrames = 0

        # repeat logic
        if self.upFrames >= config.POINT_HOLD_FRAMES:
            if (self.upFrames - config.POINT_HOLD_FRAMES) % config.POINT_REPEAT_INTERVAL == 0:
                up = True
        
        if self.downFrames >= config.POINT_HOLD_FRAMES:
            if (self.downFrames - config.POINT_HOLD_FRAMES) % config.POINT_REPEAT_INTERVAL == 0:
                dn = True

        return {"p": triggeredPinch, "vL": vL, "vR": vR, "u": up, "d": dn}

    def _gate_and_map(self, now: float, raw: dict) -> str | None:
        if now < self.cooldown:
            return None

        cmd = None
        if raw["p"]:    cmd = "toggle_play"
        elif raw["vR"]: cmd = "next"
        elif raw["vL"]: cmd = "prev"
        elif raw["u"]:  cmd = "vol_up"
        elif raw["d"]:  cmd = "vol_down"

        if cmd:
            self.prev = cmd
            self.cooldown = now + (0.1 if "vol" in cmd else config.COMMAND_COOLDOWN_S)
            return cmd
        return None
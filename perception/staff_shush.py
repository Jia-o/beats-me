import cv2
import mediapipe as mp

import config
from .engine import PerceptionEngine
from ._models import ensure_model, HAND_MODEL_URL, FACE_MODEL_URL

_vision = mp.tasks.vision
_BaseOptions = mp.tasks.BaseOptions
_RunningMode = _vision.RunningMode

_HandLandmarker = _vision.HandLandmarker
_HandLandmarkerOptions = _vision.HandLandmarkerOptions
_HandLandmarksConn = _vision.HandLandmarksConnections

_FaceLandmarker = _vision.FaceLandmarker
_FaceLandmarkerOptions = _vision.FaceLandmarkerOptions

_mp_drawing = _vision.drawing_utils
_mp_drawing_styles = _vision.drawing_styles


class StaffShushEngine(PerceptionEngine):
    """
    Staff camera engine:
    - Draw hand landmarks/lines (no blur, no segmentation).
    - Detect shush (index fingertip over lips) via FaceLandmarker + HandLandmarker.
    - Emits: { hand_present, command, mute_active }.
    """

    def __init__(self):
        super().__init__()
        self.hand = None
        self.face = None

        # gesture state (ported from HandsEngine)
        self.cooldown: float = 0.0
        self.prev: str | None = None
        self.vFrames = 0
        self.upFrames = 0
        self.downFrames = 0
        self.pinch = False

        # shush (tap-to-toggle) state
        self._shush_prev: bool = False
        self._shush_cooldown_until: float = 0.0

    def resetGestures(self):
        self.vFrames = 0
        self.upFrames = 0
        self.downFrames = 0
        self.pinch = False
        self.cooldown = 0.0
        self.prev = None
        self._shush_prev = False
        self._shush_cooldown_until = 0.0

    def _on_start(self):
        hand_model_path = ensure_model(HAND_MODEL_URL, "hand_landmarker.task")
        hand_options = _HandLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=hand_model_path),
            running_mode=_RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.hand = _HandLandmarker.create_from_options(hand_options)

        face_model_path = ensure_model(FACE_MODEL_URL, "face_landmarker.task")
        face_options = _FaceLandmarkerOptions(
            base_options=_BaseOptions(model_asset_path=face_model_path),
            running_mode=_RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.face = _FaceLandmarker.create_from_options(face_options)

        self.resetGestures()

    def _on_stop(self):
        if self.hand:
            self.hand.close()
            self.hand = None
        if self.face:
            self.face.close()
            self.face = None

    @staticmethod
    def _mouth_center(face_lms):
        # FaceMesh landmarks: 13 (upper lip), 14 (lower lip)
        up = face_lms[13]
        dn = face_lms[14]
        return ((up.x + dn.x) / 2.0, (up.y + dn.y) / 2.0)

    def classify(self, lms) -> dict:
        # (copied from HandsEngine)
        thumbTip, indexTip, middleTip, ringTip, pinkyTip = lms[4], lms[8], lms[12], lms[16], lms[20]
        indexMid, middleMid, ringMid, pinkyMid = lms[5], lms[9], lms[13], lms[17]

        cx = sum(p.x for p in [lms[i] for i in (0, 5, 9, 13, 17)]) / 5

        dist = ((thumbTip.x - indexTip.x) ** 2 + (thumbTip.y - indexTip.y) ** 2) ** 0.5
        isPinching = dist < config.PINCH_THRESHOLD

        triggeredPinch = False
        if isPinching:
            if not self.pinch:
                triggeredPinch = True
                self.pinch = True
        else:
            self.pinch = False

        idxUp, midUp = indexTip.y < indexMid.y - 0.05, middleTip.y < indexMid.y - 0.05
        rngDn, pnkDn = ringTip.y > ringMid.y, pinkyTip.y > pinkyMid.y

        vL, vR = False, False
        if idxUp and midUp and rngDn and pnkDn:
            self.vFrames += 1
            if self.vFrames >= config.POINT_HOLD_FRAMES:
                if cx < 0.4:
                    vL = True
                elif cx > 0.6:
                    vR = True
        else:
            self.vFrames = 0

        up, dn = False, False
        curled = all(t.y > m.y for t, m in [(middleTip, middleMid), (ringTip, ringMid), (pinkyTip, pinkyMid)])

        if not (idxUp and midUp):
            if indexTip.y < indexMid.y - 0.1 and curled:
                self.upFrames += 1
                self.downFrames = 0
            elif indexTip.y > indexMid.y + 0.1 and curled:
                self.downFrames += 1
                self.upFrames = 0
            else:
                self.upFrames = self.downFrames = 0

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
        if raw["p"]:
            cmd = "toggle_play"
        elif raw["vR"]:
            cmd = "next"
        elif raw["vL"]:
            cmd = "prev"
        elif raw["u"]:
            cmd = "vol_up"
        elif raw["d"]:
            cmd = "vol_down"

        if cmd:
            self.prev = cmd
            self.cooldown = now + (0.1 if "vol" in cmd else config.COMMAND_COOLDOWN_S)
            return cmd
        return None

    def process_frame(self, frame):
        res = {
            "hand_present": False,
            "command": None,
            "shush_hover": False,   # finger over lips right now
            "shush_tap": False,     # rising-edge event, debounced
        }
        if not self._active or self.hand is None or self.face is None:
            return frame, res

        out = frame.copy()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        hand = self.hand.detect(mp_img)
        if not hand.hand_landmarks:
            self.resetGestures()
            return out, res

        lms = hand.hand_landmarks[0]
        res["hand_present"] = True

        _mp_drawing.draw_landmarks(
            out,
            lms,
            _HandLandmarksConn.HAND_CONNECTIONS,
            _mp_drawing_styles.get_default_hand_landmarks_style(),
            _mp_drawing_styles.get_default_hand_connections_style(),
        )

        import time as _time
        now = _time.time()

        # Detect shush hover first so we can suppress vol-up while shushing.
        face = self.face.detect(mp_img)
        if face.face_landmarks:
            mx, my = self._mouth_center(face.face_landmarks[0])
            idx_tip = lms[8]
            dx = abs(idx_tip.x - mx)
            dy = abs(idx_tip.y - my)
            shush = (dx <= config.SHUSH_MOUTH_X_THRESH) and (dy <= config.SHUSH_MOUTH_Y_THRESH)
            res["shush_hover"] = bool(shush)

            # Rising-edge "tap" event (like pinch) with debounce window.
            if shush and (not self._shush_prev) and (now >= self._shush_cooldown_until):
                res["shush_tap"] = True
                self._shush_cooldown_until = now + config.COMMAND_COOLDOWN_S
            self._shush_prev = bool(shush)

        raw = self.classify(lms)
        cmd = self._gate_and_map(now, raw)

        # While finger is over lips, don't allow "volume up" to fire.
        if res["shush_hover"] and cmd == "vol_up":
            cmd = None

        res["command"] = cmd
        return out, res


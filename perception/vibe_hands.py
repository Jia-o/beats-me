import time
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

import config
from .engine import PerceptionEngine
from ._models import ensure_model, HAND_MODEL_URL, SELFIE_SEGMENTER_MODEL_URL

_vision = mp.tasks.vision
_BaseOptions = mp.tasks.BaseOptions
_RunningMode = _vision.RunningMode

_HandLandmarker = _vision.HandLandmarker
_HandLandmarkerOptions = _vision.HandLandmarkerOptions
_HandLandmarksConn = _vision.HandLandmarksConnections

_ImageSegmenter = _vision.ImageSegmenter
_ImageSegmenterOptions = _vision.ImageSegmenterOptions

_mp_drawing = _vision.drawing_utils
_mp_drawing_styles = _vision.drawing_styles


class VibeHandsEngine(PerceptionEngine):
    """
    Vision pipeline:
    - Selfie segmentation generates a 'me' alpha mask.
    - Background is either (a) blurred album art from Spotify or (b) blurred room.
    - Composite: blurred bg (bottom) + me (middle) + hand lines (top).
    """

    def __init__(self, background_provider=None):
        super().__init__()
        self._background_provider = background_provider  # callable() -> np.ndarray|None (BGR)

        self.hand_landmarker = None
        self.segmenter = None

        # gesture state (ported from HandsEngine)
        self.cooldown: float = 0.0
        self.prev: str | None = None
        self.vFrames = 0
        self.upFrames = 0
        self.downFrames = 0
        self.pinch = False

        # segmentation smoothing
        self._prev_alpha: np.ndarray | None = None

        # album art cache (only used if provider returns URLs rather than images)
        self._album_cache_url: str | None = None
        self._album_cache_bgr: np.ndarray | None = None
        self._album_cache_ts: float = 0.0

    def resetGestures(self):
        self.vFrames = 0
        self.upFrames = 0
        self.downFrames = 0
        self.pinch = False
        self.cooldown = 0.0
        self.prev = None

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
        self.hand_landmarker = _HandLandmarker.create_from_options(hand_options)

        seg_model_path = ensure_model(SELFIE_SEGMENTER_MODEL_URL, "selfie_segmenter.tflite")
        seg_options = _ImageSegmenterOptions(
            base_options=_BaseOptions(model_asset_path=seg_model_path),
            running_mode=_RunningMode.IMAGE,
            output_category_mask=True,
            output_confidence_masks=True,
        )
        self.segmenter = _ImageSegmenter.create_from_options(seg_options)

        self.resetGestures()
        self._prev_alpha = None

    def _on_stop(self):
        if self.hand_landmarker:
            self.hand_landmarker.close()
            self.hand_landmarker = None
        if self.segmenter:
            self.segmenter.close()
            self.segmenter = None
        self._prev_alpha = None

    # ---------------------------- background ----------------------------

    def _get_album_art_bgr(self, url: str) -> np.ndarray | None:
        now = time.time()
        if (
            self._album_cache_url == url
            and self._album_cache_bgr is not None
            and (now - self._album_cache_ts) < config.ALBUM_ART_CACHE_S
        ):
            return self._album_cache_bgr
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                data = resp.read()
            arr = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return None
            self._album_cache_url = url
            self._album_cache_bgr = img
            self._album_cache_ts = now
            return img
        except Exception:
            return None

    def _get_blurred_background(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Provider can return:
        - np.ndarray (BGR) album art image
        - str URL to album art
        - None (no music) -> use blurred room
        """
        h, w = frame_bgr.shape[:2]

        src = None
        if callable(self._background_provider):
            try:
                src = self._background_provider()
            except Exception:
                src = None

        bg = None
        if isinstance(src, str) and src.strip():
            bg = self._get_album_art_bgr(src.strip())
        elif isinstance(src, np.ndarray):
            bg = src

        if bg is None:
            bg = frame_bgr

        bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_LINEAR)
        # Massive blur for soft vibe background.
        return cv2.GaussianBlur(bg, (0, 0), sigmaX=config.VIBE_BG_BLUR_SIGMA, sigmaY=config.VIBE_BG_BLUR_SIGMA)

    # ---------------------------- segmentation ----------------------------

    def _get_person_alpha(self, frame_bgr: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        seg = self.segmenter.segment(mp_img)
        alpha = None

        # Prefer confidence mask (per-pixel probability) when available.
        try:
            if getattr(seg, "confidence_masks", None):
                # For selfie segmenter, index 0 corresponds to the person class.
                alpha = seg.confidence_masks[0].numpy_view().astype(np.float32)
        except Exception:
            alpha = None

        if alpha is None:
            # Fallback: category mask (per-pixel class index).
            mask = seg.category_mask.numpy_view()
            alpha = (mask.astype(np.float32) > 0.5).astype(np.float32)

        # Edge smoothing to reduce flicker/jitter.
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=config.SEG_EDGE_BLUR_SIGMA, sigmaY=config.SEG_EDGE_BLUR_SIGMA)
        alpha = np.clip(alpha, 0.0, 1.0)

        if self._prev_alpha is None or self._prev_alpha.shape != alpha.shape:
            self._prev_alpha = alpha
            return alpha

        # Temporal smoothing (EMA).
        a = config.SEG_TEMPORAL_SMOOTH_ALPHA
        smoothed = (1.0 - a) * self._prev_alpha + a * alpha
        self._prev_alpha = smoothed
        return smoothed

    # ---------------------------- gestures (ported) ----------------------------

    def classify(self, lms) -> dict:
        thumbTip, indexTip, middleTip, ringTip, pinkyTip = lms[4], lms[8], lms[12], lms[16], lms[20]
        indexMid, middleMid, ringMid, pinkyMid = lms[5], lms[9], lms[13], lms[17]

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
                if cx < 0.4:
                    vL = True
                elif cx > 0.6:
                    vR = True
        else:
            self.vFrames = 0

        up, dn = False, False
        curled = all(t.y > m.y for t, m in [(middleTip, middleMid), (ringTip, ringMid), (pinkyTip, pinkyMid)])

        if not (idxUp and midUp):  # skip if v-sign active
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

    # ---------------------------- main loop ----------------------------

    def process_frame(self, frame):
        res = {
            "hand_present": False,
            "command": None,
            "mute_active": False,
            "debug": {},
        }
        if not self._active or self.hand_landmarker is None or self.segmenter is None:
            return frame, res

        bg = self._get_blurred_background(frame)
        alpha = self._get_person_alpha(frame)  # HxW float32

        # Composite: bg (bottom) + me (middle)
        a3 = alpha[:, :, None]
        composite = (bg.astype(np.float32) * (1.0 - a3) + frame.astype(np.float32) * a3).astype(np.uint8)

        # Hands (top)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detect = self.hand_landmarker.detect(mp_img)

        out = composite
        if not detect.hand_landmarks:
            self.resetGestures()
            return out, res

        lms = detect.hand_landmarks[0]
        res["hand_present"] = True

        _mp_drawing.draw_landmarks(
            out,
            lms,
            _HandLandmarksConn.HAND_CONNECTIONS,
            _mp_drawing_styles.get_default_hand_landmarks_style(),
            _mp_drawing_styles.get_default_hand_connections_style(),
        )

        now = time.time()
        raw = self.classify(lms)
        cmd = self._gate_and_map(now, raw)
        res["command"] = cmd
        return out, res


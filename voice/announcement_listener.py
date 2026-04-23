import time
import threading
from dataclasses import dataclass

import config


@dataclass(frozen=True)
class AnnouncementMeta:
    phrase: str | None
    text: str | None


class AnnouncementListener:
    """
    Best-effort speech listener.

    Behavior:
    - When any configured phrase is recognized, fires on_announcement_start().
    - While "in announcement", waits for speech to settle (silence/low energy) for
      a window, then fires on_announcement_end().

    Implementation notes:
    - Uses Vosk + sounddevice if available and a model path is configured.
    - If dependencies/model aren't available, it self-disables (no-op).
    """

    def __init__(self, phrases, on_announcement_start, on_announcement_end,
                 on_ducking_start=None, on_ducking_end=None):
        self._phrases = [p.strip().lower() for p in (phrases or []) if p.strip()]
        self._on_start = on_announcement_start
        self._on_end = on_announcement_end
        self._on_ducking_start = on_ducking_start
        self._on_ducking_end = on_ducking_end

        self._enabled = True
        self._running = False
        self._thread: threading.Thread | None = None

        self._in_announcement = False
        self._ducking = False
        self._last_speech_ts = 0.0

        # Lazy imports so the rest of the app works without audio deps.
        self._vosk = None
        self._sd = None
        self._json = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    # ---------------------------- internals ----------------------------

    def _disable(self, reason: str):
        if self._enabled:
            print(f"[voice] announcement listener disabled: {reason}")
        self._enabled = False

    def _maybe_init_backend(self) -> bool:
        if not self._enabled:
            return False

        if not config.VOSK_MODEL_PATH:
            self._disable("VOSK_MODEL_PATH not set in config.py")
            return False

        try:
            import json
            import vosk
            import sounddevice as sd
        except Exception as exc:
            self._disable(f"missing dependency ({exc})")
            return False

        self._json = json
        self._vosk = vosk
        self._sd = sd
        return True

    def _run(self):
        if not self._maybe_init_backend():
            return

        vosk = self._vosk
        sd = self._sd
        json = self._json

        try:
            model = vosk.Model(config.VOSK_MODEL_PATH)
            rec = vosk.KaldiRecognizer(model, config.VOICE_SAMPLE_RATE)
        except Exception as exc:
            self._disable(f"failed to load Vosk model ({exc})")
            return

        q: list[bytes] = []

        def _callback(indata, frames, time_info, status):
            if status:
                return
            q.append(bytes(indata))

        try:
            with sd.RawInputStream(
                samplerate=config.VOICE_SAMPLE_RATE,
                blocksize=config.VOICE_BLOCK_SIZE,
                dtype="int16",
                channels=1,
                callback=_callback,
            ):
                while self._running:
                    if not q:
                        time.sleep(0.01)
                        self._maybe_end_announcement()
                        continue

                    data = q.pop(0)
                    if rec.AcceptWaveform(data):
                        msg = json.loads(rec.Result() or "{}")
                        text = (msg.get("text") or "").strip().lower()
                        if text:
                            self._on_text(text)
                    else:
                        msg = json.loads(rec.PartialResult() or "{}")
                        text = (msg.get("partial") or "").strip().lower()
                        if text:
                            self._on_text(text, partial=True)

                    self._maybe_end_announcement()
        except Exception as exc:
            self._disable(f"audio stream failed ({exc})")

    def _on_text(self, text: str, partial: bool = False):
        now = time.time()
        self._last_speech_ts = now

        # Ducking: fire on the first detection of any speech while not already ducking.
        if not self._ducking and self._on_ducking_start:
            self._ducking = True
            try:
                self._on_ducking_start({"partial": partial, "text": text})
            except Exception:
                pass

        if not self._phrases:
            return

        # Simple substring match; robust enough for key phrases.
        matched = next((p for p in self._phrases if p in text), None)
        if matched and not self._in_announcement:
            self._in_announcement = True
            meta = AnnouncementMeta(phrase=matched, text=text)
            try:
                self._on_start({"phrase": meta.phrase, "text": meta.text})
            except Exception:
                pass

    def _maybe_end_announcement(self):
        if not self._in_announcement and not self._ducking:
            return
        now = time.time()
        if (now - self._last_speech_ts) >= config.ANNOUNCEMENT_END_SILENCE_S:
            # Track whether the announcement ended in this same pass so we can
            # avoid firing _on_ducking_end redundantly (the announcement_end
            # callback already handles recovery for that path).
            announcement_ended = False
            if self._in_announcement:
                self._in_announcement = False
                announcement_ended = True
                try:
                    self._on_end({"reason": "silence_window"})
                except Exception:
                    pass
            if self._ducking:
                self._ducking = False
                # Only fire ducking_end when the announcement didn't also end
                # here; when both end together the announcement_end callback
                # already covers volume recovery.
                if self._on_ducking_end and not announcement_ended:
                    try:
                        self._on_ducking_end({"reason": "silence_window"})
                    except Exception:
                        pass

"""
perception/engine.py – abstract base class for all perception engines.

Concrete engines (HandsEngine, PoseEngine, FaceEngine) inherit from this and
override _on_start / _on_stop / process_frame.  The active flag is used by
the camera loop to decide whether to call process_frame at all, which lets
us avoid wasting CPU on models that aren't needed for the current mode.
"""

from collections import deque


class PerceptionEngine:
    """Base class – handles the active/inactive lifecycle."""

    def __init__(self):
        self._active = False
        self.shush_active: bool = False
        self.background_mask: deque = deque(maxlen=5)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Activate this engine and initialise the underlying MediaPipe model."""
        self._active = True
        self._on_start()

    def stop(self):
        """Deactivate and release the underlying MediaPipe model."""
        self._active = False
        self._on_stop()

    def _on_start(self):
        """Override to allocate MediaPipe resources."""

    def _on_stop(self):
        """Override to release MediaPipe resources."""

    def close(self):
        """Alias for stop(); called when the object is discarded."""
        self.stop()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active(self) -> bool:
        return self._active

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame):
        """
        Process one BGR frame.

        Returns
        -------
        annotated_frame : np.ndarray
            A copy of *frame* with MediaPipe landmarks drawn on it.
        result : dict
            Mode-specific detection result, e.g. ``{"gesture": "pinch"}``.
        """
        raise NotImplementedError

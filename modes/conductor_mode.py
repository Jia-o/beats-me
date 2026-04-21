import config
import math
# pinch        → toggle play/pause
# swipe_left   → previous track
# swipe_right  → next track
# point_up     → volume up 
# point_down   → volume down

class ConductorMode:
    def __init__(self, controller):
        self._ctrl = controller
        self.fingertips = [4, 8, 12, 16, 20] # thumb, index, middle, ring, pinky
        self.prev = None
    
    def fingers(self, landmarks):
        signs = []
        if landmarks.landmark[4].x > landmarks.landmark[3].x:
            signs.append(4)
        for i in range(1, 5):
            if landmarks.landmark[self.fingertips[i]].y < landmarks.landmark[self.fingertips[i] - 2].y:
                signs.append(self.fingertips[i])
        return signs

    def handle(self, gesture: str | None):
        if gesture is None:
            return

        if gesture == "pinch":
            self._ctrl.toggle_play()
        elif gesture == "left":
            self._ctrl.previous_track()
        elif gesture == "right":
            self._ctrl.next_track()
        elif gesture == "up":
            self._ctrl.adjust_volume(config.VOLUME_STEP)
        elif gesture == "down":
            self._ctrl.adjust_volume(-config.VOLUME_STEP)
    
    def process(self, landmarks):
        indexTip = landmarks.landmark[8]
        indexBottom = landmarks.landmark[5]
        thumbTip = landmarks.landmark[4]

        # thumb tip touching index tip 
        distance = math.sqrt((indexTip.x - thumbTip.x)**2 + (indexTip.y - thumbTip.y)**2)
        if distance < 0.05:
            return self.handle("pinch")

        # wrist direction 
        curr = landmarks.landmark[0].x
        swipe = None
        if self.prev:
            if curr - self.prev > 0.1:
                swipe = "right"
            elif self.prev - curr > 0.1:
                swipe = "left"
        self.prev = curr        
        if swipe:
            return self.handle(swipe)
        
        # tip above / below knuckle
        if indexTip.y < indexBottom.y - 0.1: 
            return self.handle("up")
        elif indexTip.y > indexBottom.y + 0.1:
            return self.handle("down")
        
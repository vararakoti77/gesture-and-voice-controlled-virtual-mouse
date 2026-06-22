import cv2
import math
import numpy as np
import os
import sys
import math
import numpy as np
import os
import sys

# Try to import mediapipe with the new Tasks API first, fall back to legacy
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    USE_TASKS_API = True
except ImportError:
    import mediapipe as mp
    USE_TASKS_API = False

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = int(maxHands)
        self.detectionCon = float(detectionCon)
        self.trackCon = float(trackCon)
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []
        self.results = None
        self.gesture_history = []
        self.palm_center = None
        self.previous_palm_center = None
        
        if USE_TASKS_API:

            # Use new MediaPipe Tasks API
            # Download the hand landmarker model if not exists
            if getattr(sys, 'frozen', False):
                # If the application is run as a bundle, the PyInstaller bootloader
                # extends the sys module by a flag frozen=True and sets the app 
                # path into variable _MEIPASS'.
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            model_path = os.path.join(application_path, 'hand_landmarker.task')
            
            if not os.path.exists(model_path):
                import urllib.request
                print("Downloading hand landmarker model...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
                print("Model downloaded successfully!")
            
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=self.maxHands,
                min_hand_detection_confidence=self.detectionCon,
                min_tracking_confidence=self.trackCon
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
        else:
            # Use legacy API
            if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "hands"):
                raise RuntimeError(
                    "MediaPipe legacy solutions are unavailable in this installation."
                    " Please install mediapipe==0.9.* to use the legacy pipeline."
                )
            self.mpHands = mp.solutions.hands
            self.hands = self.mpHands.Hands(
                static_image_mode=self.mode,
                max_num_hands=self.maxHands,
                min_detection_confidence=self.detectionCon,
                min_tracking_confidence=self.trackCon
            )
            self.mpDraw = mp.solutions.drawing_utils
            self.mp_hands_connections = self.mpHands.HAND_CONNECTIONS

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        if USE_TASKS_API:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
            self.results = self.detector.detect(mp_image)
            
            if self.results.hand_landmarks and draw:
                h, w, c = img.shape
                for hand_landmarks in self.results.hand_landmarks:
                    # Draw connections
                    landmarks_px = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
                    for conn in HAND_CONNECTIONS:
                        cv2.line(img, landmarks_px[conn[0]], landmarks_px[conn[1]], (0, 255, 0), 2)
                    for lm_px in landmarks_px:
                        cv2.circle(img, lm_px, 5, (255, 0, 255), cv2.FILLED)
        else:
            self.results = self.hands.process(imgRGB)
            if self.results.multi_hand_landmarks:
                for handLms in self.results.multi_hand_landmarks:
                    if draw:
                        self.mpDraw.draw_landmarks(img, handLms, self.mp_hands_connections)

        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []
        
        if USE_TASKS_API:
            if self.results and self.results.hand_landmarks:
                if handNo < len(self.results.hand_landmarks):
                    myHand = self.results.hand_landmarks[handNo]
                    h, w, c = img.shape
                    for id, lm in enumerate(myHand):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        xList.append(cx)
                        yList.append(cy)
                        self.lmList.append([id, cx, cy])
                        if draw:
                            cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                    if xList and yList:
                        xmin, xmax = min(xList), max(xList)
                        ymin, ymax = min(yList), max(yList)
                        bbox = xmin, ymin, xmax, ymax

                        if draw:
                            cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)
        else:
            if self.results.multi_hand_landmarks:
                myHand = self.results.multi_hand_landmarks[handNo]
                for id, lm in enumerate(myHand.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    xList.append(cx)
                    yList.append(cy)
                    self.lmList.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                bbox = xmin, ymin, xmax, ymax

                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)

        return self.lmList, bbox

    def fingersUp(self):
        fingers = []
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers
    
    def getPalmCenter(self):
        """Get the center of the palm"""
        if len(self.lmList) != 0:
            # Use landmarks 0 (wrist) and 9 (middle finger base) to calculate palm center
            palm_x = (self.lmList[0][1] + self.lmList[9][1]) // 2
            palm_y = (self.lmList[0][2] + self.lmList[9][2]) // 2
            self.palm_center = (palm_x, palm_y)
            return self.palm_center
        return None
    
    def isPalmOpen(self):
        """Check if palm is fully open (all fingers extended)"""
        fingers = self.fingersUp()
        return sum(fingers) >= 4
    
    def isPalmClosed(self):
        """Check if palm is closed (fist)"""
        fingers = self.fingersUp()
        return sum(fingers) == 0
    
    def getPinchDistance(self, finger_tip_id=8):
        """Get distance between thumb and specified finger tip (default: index)"""
        if len(self.lmList) != 0:
            thumb_tip = self.lmList[4]
            finger_tip = self.lmList[finger_tip_id]
            distance = math.hypot(finger_tip[1] - thumb_tip[1], finger_tip[2] - thumb_tip[2])
            return distance
        return 999
    
    def isPinching(self, threshold=40, finger_tip_id=8):
        """Check if thumb and finger are pinching"""
        distance = self.getPinchDistance(finger_tip_id)
        return distance < threshold

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]
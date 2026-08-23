from __future__ import annotations

import cv2
import numpy as np


class MotionDetector:
    def __init__(self, minimum_area: int = 900):
        self.minimum_area = minimum_area
        self._subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300,
            varThreshold=32,
            detectShadows=False,
        )

    def process(self, frame: np.ndarray) -> tuple[np.ndarray, bool]:
        mask = self._subtractor.apply(frame)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion = False
        output = frame.copy()
        for contour in contours:
            if cv2.contourArea(contour) < self.minimum_area:
                continue
            motion = True
            x, y, width, height = cv2.boundingRect(contour)
            cv2.rectangle(output, (x, y), (x + width, y + height), (42, 196, 126), 2)
        return output, motion

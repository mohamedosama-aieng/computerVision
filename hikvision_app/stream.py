from __future__ import annotations

import os
import time

# OpenCV reads this option when its FFmpeg backend is initialized.
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .vision import MotionDetector


class StreamWorker(QThread):
    frame_ready = Signal(QImage)
    state_changed = Signal(str)

    def __init__(self, url: str, detect_motion: bool = False, parent=None):
        super().__init__(parent)
        self._url = url
        self._detect_motion = detect_motion
        self._running = True

    def run(self) -> None:
        detector = MotionDetector() if self._detect_motion else None
        retry_delay = 1.0
        while self._running:
            self.state_changed.emit("Opening RTSP")
            capture = cv2.VideoCapture(self._url, cv2.CAP_FFMPEG)
            capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
            capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not capture.isOpened():
                self.state_changed.emit("RTSP unavailable")
                capture.release()
                self._sleep_interruptibly(retry_delay)
                retry_delay = min(retry_delay * 2, 15.0)
                continue

            self.state_changed.emit("Waiting for video")
            retry_delay = 1.0
            while self._running:
                success, frame = capture.read()
                if not success:
                    self.state_changed.emit("No video frames")
                    break
                if detector:
                    frame, motion = detector.process(frame)
                    self.state_changed.emit("Motion" if motion else "Live")
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channels = rgb.shape
                image = QImage(rgb.data, width, height, channels * width, QImage.Format.Format_RGB888)
                self.frame_ready.emit(image.copy())
            capture.release()
        self.state_changed.emit("Stopped")

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()

    def _sleep_interruptibly(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while self._running and time.monotonic() < deadline:
            self.msleep(100)

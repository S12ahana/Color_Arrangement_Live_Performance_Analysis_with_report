import av
import cv2
import time
import numpy as np
from streamlit_webrtc import VideoProcessorBase


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False

        # 🔐 Identity
        self.identity_matched = True
        self.reference_face = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # =========================
        # FACE-BASED IDENTITY CHECK
        # =========================
        if self.reference_face is not None:
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                x, y, w, h = faces[0]
                live_face = gray[y:y+h, x:x+w]
                live_face = cv2.resize(live_face, (200, 200))

                diff = cv2.absdiff(self.reference_face, live_face)
                score = np.mean(diff)

                # 🎯 Threshold (tune if needed)
                self.identity_matched = score < 60
            else:
                self.identity_matched = False

        # =========================
        # MOTION (ONLY FOR COLOR)
        # =========================
        if not self.bg_saved:
            self.prev_gray = gray
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        if self.prev_gray is not None:
            diff = cv2.absdiff(self.prev_gray, gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            motion_pixels = cv2.countNonZero(thresh)

            if motion_pixels > 2000:
                self.last_motion_time = time.time()

        # ⚠️ PLACE COLOR WARNING
        if time.time() - self.last_motion_time > 3:
            cv2.putText(
                img,
                "⚠️ PLACE THE COLOR!",
                (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

        # 🚫 IDENTITY MISMATCH (FACE ONLY)
        if not self.identity_matched:
            cv2.putText(
                img,
                "🚫 IDENTITY MISMATCH",
                (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )
            cv2.rectangle(
                img,
                (20, 20),
                (img.shape[1] - 20, img.shape[0] - 20),
                (0, 0, 255),
                4
            )

        self.prev_gray = gray
        return av.VideoFrame.from_ndarray(img, format="bgr24")
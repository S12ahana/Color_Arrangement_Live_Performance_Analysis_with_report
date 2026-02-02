import av
import cv2
from streamlit_webrtc import VideoProcessorBase
import time
from utils.face_recognition_utils 
import verify_face  # Assume you have a helper to match faces


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False
        self.mismatch_count = 0
        self.verification_status = "Unknown"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # -------- INITIALIZATION --------
        if not self.bg_saved:
            self.prev_gray = gray
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        if self.prev_gray is None:
            self.prev_gray = gray
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        # -------- MOTION DETECTION --------
        diff = cv2.absdiff(self.prev_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        motion_pixels = cv2.countNonZero(thresh)

        if motion_pixels > 2000:
            self.last_motion_time = time.time()
        else:
            self.mismatch_count += 1

        # -------- FACE VERIFICATION --------
        if hasattr(self, "registered_face") and self.registered_face is not None:
            match = verify_face(img, self.registered_face)
            if match:
                self.verification_status = "Matched"
            else:
                self.verification_status = "Mismatch"

        # -------- OVERLAY MESSAGES --------
        if time.time() - self.last_motion_time > 3:
            cv2.putText(img, "⚠️ PLACE THE COLOR!", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            cv2.rectangle(img, (10, 10),
                          (img.shape[1]-10, img.shape[0]-10),
                          (0, 0, 255), 4)

        # Live identity verification overlay
        status_text = "✅ Verified" if self.verification_status == "Matched" else "🚫 Identity Mismatch"
        status_color = (0, 255, 0) if self.verification_status == "Matched" else (0, 0, 255)
        cv2.putText(img, status_text, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

        self.prev_gray = gray
        return av.VideoFrame.from_ndarray(img, format="bgr24")
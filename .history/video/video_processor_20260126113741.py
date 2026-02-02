import av
import cv2
import time
from streamlit_webrtc import VideoProcessorBase


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False

        # Face verification
        self.reference_face = None   # login face
        self.background_face = None  # background face
        self.identity_matched = True

    # ==============================
    # FACE COMPARISON (MSE)
    # ==============================
    def compare_faces(self):
        if self.reference_face is None or self.background_face is None:
            return True  # don't block early

        ref = self.reference_face
        bg = self.background_face

        # Ensure grayscale
        if len(ref.shape) == 3:
            ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
        if len(bg.shape) == 3:
            bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)

        ref = cv2.resize(ref, (200, 200))
        bg = cv2.resize(bg, (200, 200))

        mse = ((ref.astype("float") - bg.astype("float")) ** 2).mean()
        print("Face MSE:", mse)

        return mse < 2000  # threshold

    # ==============================
    # VIDEO STREAM
    # ==============================
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if not self.bg_saved:
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

        # -------- FACE CHECK --------
        self.identity_matched = self.compare_faces()

        if not self.identity_matched:
            cv2.putText(
                img,
                "🚫 FACE MISMATCH",
                (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

        self.prev_gray = gray
        return av.VideoFrame.from_ndarray(img, format="bgr24")
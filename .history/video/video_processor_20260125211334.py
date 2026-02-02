import av
import cv2
from streamlit_webrtc import VideoProcessorBase
import time


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.prev_gray = None
        self.last_motion_time = time.time()
        self.bg_saved = False
        self.mismatch_count = 0

    def recv(self, frame):
    img = frame.to_ndarray(format="bgr24")
    self.frame = img.copy()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if not self.bg_saved:
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    if self.prev_gray is None:
        self.prev_gray = gray
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    diff = cv2.absdiff(self.prev_gray, gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    motion_pixels = cv2.countNonZero(thresh)

    if motion_pixels > 2000:
        self.last_motion_time = time.time()
    else:
        self.mismatch_count += 1

    # ----- Show place color warning -----
    if time.time() - self.last_motion_time > 3:
        cv2.putText(img, "⚠️ PLACE THE COLOR!", (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255), 3)
        cv2.rectangle(img, (10, 10),
                      (img.shape[1]-10, img.shape[0]-10),
                      (0, 0, 255), 4)

    # ----- LIVE IDENTITY VERIFICATION STATUS -----
    if self.mismatch_count > 0:
        status_text = "🚫 Identity Mismatch"
        color = (0, 0, 255)  # Red
    else:
        status_text = "✅ Verified"
        color = (0, 255, 0)  # Green

    cv2.putText(
        img,
        status_text,
        (10, 40),  # top-left, below warning if any
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        2
    )

    self.prev_gray = gray
    return av.VideoFrame.from_ndarray(img, format="bgr24")
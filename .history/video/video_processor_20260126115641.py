import cv2
import numpy as np
from streamlit_webrtc import VideoProcessorBase

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None
        self.reference_face = None      # Registered login face
        self.background_face = None
        self.bg_saved = False
        self.identity_matched = False

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img.copy()

        # If reference face exists, check face match
        if self.reference_face is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            ).detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                x, y, w, h = faces[0]
                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face, (200, 200))

                # Compare with registered face
                self.identity_matched = self.compare_faces(face, self.reference_face)
            else:
                self.identity_matched = False

        return frame

    @staticmethod
    def compare_faces(face1, face2):
        """
        Simple mean squared error comparison
        Returns True if faces match
        """
        if face1.shape != face2.shape:
            return False
        error = np.sum((face1.astype("float") - face2.astype("float")) ** 2)
        return error < 2500   # Threshold for face match
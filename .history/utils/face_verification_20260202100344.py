import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def extract_face(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return None

    x, y, w, h = faces[0]
    face = img[y:y+h, x:x+w]
    face = cv2.resize(face, (200, 200))
    return face

def verify_face(registered_img, live_img):
    reg_face = extract_face(registered_img)
    live_face = extract_face(live_img)

    if reg_face is None or live_face is None:
        return False

    diff = cv2.absdiff(reg_face, live_face)
    score = np.mean(diff)

    return score < 40   
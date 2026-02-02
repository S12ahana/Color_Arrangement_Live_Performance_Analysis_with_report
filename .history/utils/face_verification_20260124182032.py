import face_recognition
import cv2

def verify_face(known_encoding, frame, tolerance=0.5):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_encodings(rgb)

    if len(faces) == 0:
        return False, "No Face"

    match = face_recognition.compare_faces(
        [known_encoding], faces[0], tolerance=tolerance
    )[0]

    return match, "Matched" if match else "Mismatch"
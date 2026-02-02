import cv2
import numpy as np

def detect_colors(frame):
    colors = {
        "Red": ((0, 120, 70), (10, 255, 255)),
        "Blue": ((94, 80, 2), (126, 255, 255)),
        "Green": ((40, 40, 40), (70, 255, 255))
    }

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    detected = {}

    for color, (lower, upper) in colors.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            detected[color] = (x + w // 2, y + h // 2)

    return detected
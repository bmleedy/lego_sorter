import numpy as np
import cv2

WINDOW_NAME = "Pick_a_point"
FONT_MULTIPLIER = 0.5
orig_image = cv2.imread("test.jpg")

# Args: event, x, y, flags, userdata)
def pick_point(event, x, y, flags, userdata):
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    image=orig_image.copy()
    imageHSV = cv2.cvtColor(orig_image, cv2.COLOR_BGR2HSV)   
    hsv = imageHSV[y,x]
    h = hsv[0]
    s = hsv[1]
    v = hsv[2]

    cv2.putText(
            image,f"hue: {h}", 
            (int(round(6*FONT_MULTIPLIER)), int(round(30*FONT_MULTIPLIER))),
            cv2.FONT_HERSHEY_SIMPLEX, 
            FONT_MULTIPLIER,
            (0,255,0),
            int(round(2.5*FONT_MULTIPLIER)),
            8,
            False)
    cv2.putText(image,f"sat: {s}",
            (int(round(6*FONT_MULTIPLIER)), int(round(2*30*FONT_MULTIPLIER))),
            cv2.FONT_HERSHEY_SIMPLEX, 
            FONT_MULTIPLIER,
            (0,255,0),
            int(round(2.5*FONT_MULTIPLIER)),
            8,
            False)
    cv2.putText(image,f"val: {v}",
            (int(round(6*FONT_MULTIPLIER)), int(round(3*30*FONT_MULTIPLIER))),
            cv2.FONT_HERSHEY_SIMPLEX, 
            FONT_MULTIPLIER,
            (0,255,0),
            int(round(2.5*FONT_MULTIPLIER)),
            8,
            False)
    cv2.putText(image,f"X: {x}  Y:  {y}",
            (int(round(6*FONT_MULTIPLIER)), int(round(4*30*FONT_MULTIPLIER))),
            cv2.FONT_HERSHEY_SIMPLEX, 
            FONT_MULTIPLIER,
            (0,255,0),
            int(round(2.5*FONT_MULTIPLIER)),
            8,
            False)
    
    cv2.imshow(WINDOW_NAME, image)

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, 800,800)
cv2.imshow(WINDOW_NAME, orig_image)
cv2.setMouseCallback(WINDOW_NAME, pick_point)
cv2.waitKey()

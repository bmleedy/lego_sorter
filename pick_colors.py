import numpy as np
import cv2

WINDOW_NAME = "Pick_a_point"

orig_image = cv2.imread("yellow.jpg")

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

    cv2.putText(image,f"hue: {h}", (25,120) , cv2.FONT_HERSHEY_SIMPLEX, 4, (0,255,0), 5,8, False )
    cv2.putText(image,f"sat: {s}", (25,240) , cv2.FONT_HERSHEY_SIMPLEX, 4, (0,255,0), 5,8, False )
    cv2.putText(image,f"val: {v}", (25,360) , cv2.FONT_HERSHEY_SIMPLEX, 4, (0,255,0), 5,8, False )
    cv2.putText(image,f"X: {x}  Y:  {y}", (25, 480), cv2.FONT_HERSHEY_SIMPLEX, 4, (0,2550), 5, 8, False)
    
    cv2.imshow(WINDOW_NAME, image)

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, 800,800)
cv2.imshow(WINDOW_NAME, orig_image)
cv2.setMouseCallback(WINDOW_NAME, pick_point)
cv2.waitKey()

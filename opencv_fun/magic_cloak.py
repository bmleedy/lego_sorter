#!/bin/python3
"""This is the magic cloak USB camera code"""

import os
import json
import time
from datetime import datetime
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import numpy as np

# GPIO Imports
import RPi.GPIO as GPIO

# constants for tweaking
LIVE_WINDOW_NAME = "Live View"
BACKGROUND_WINDOW_NAME = "Background"
SCALE_PERCENT = 20
PIXEL_THRESHOLD = 50
RANGE_PADDING = 10
SHOW_OVERLAY = True
COLOR_COLUMN_WIDTH = 10
OUTPUT_VIDEO = False
VIDEO_NAME = "output.avi"
LEGO_CONFIG_NAME = "legos.config.json"
GROW_PIXELS = 3
PHOTO_INTERVAL = 10.0

cap = cv2.VideoCapture(0)


print("starting in:")
for i in range(1,3):
    print(f"{i} ...")
    time.sleep(1.0)
print("go!")


ret, background_image = cap.read()
background_image=cv2.flip(background_image, 1)


cv2.imshow(BACKGROUND_WINDOW_NAME, background_image)
cv2.waitKey(1)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(f'/tmp/images/cloak_vid_{datetime.now()}.avi', fourcc, 10.0, (640, 480))

nowtime = time.clock()
vidtime = time.clock()

while(True):
    os.system('clear')

    ret, frame = cap.read()
    
    frame = cv2.flip(frame, 1)
    image_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Find the mask for where it's red

    recognition_mask = cv2.inRange(
        image_hsv,
        np.array([160,150,70]),
        np.array([180,255,255]))

    recognition_mask_other = cv2.inRange(
            image_hsv,
            np.array([0,180,70]),
            np.array([20,255,255]))

    recognition_mask += recognition_mask_other

    # get rid of speckles on the recognition field
    recognition_mask = cv2.medianBlur(recognition_mask, 3)

    recognition_indices = np.where(recognition_mask > 0)

    frame[recognition_indices]=background_image[recognition_indices] 

    # Write out an image frame to a jpg in /tmp/images
    if((time.clock() - nowtime) >= PHOTO_INTERVAL):
        cv2.imwrite(f"/tmp/images/cloak_{datetime.now()}.jpg",frame)
        nowtime = time.clock()

    # Write video frames to a file
    if((time.clock() - vidtime) >= 0.1):
        out.write(frame)
        vidtime = time.clock()

    print(datetime.now())
    print(f"last image captured on: {nowtime}: {datetime.now()}")
    print(f"now it is: {time.clock()}")

    # write an image to a file, if my 10 second timer is up
    cv2.imshow(LIVE_WINDOW_NAME, frame)
    cv2.waitKey(1)



cap.release()
cv2.destroyAllWindows()

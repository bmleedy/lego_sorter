#!/bin/python3
"""This is the magic cloak USB camera code. A quick-and-dirty
    program to turn red objects into magical invisibility
    material."""

import os
import time
from datetime import datetime
import cv2
import numpy as np

# Constants for tweaking
LIVE_WINDOW_NAME = "Live View"
BACKGROUND_WINDOW_NAME = "Background"
PHOTO_INTERVAL = 10.0
DESPECKLE_KERNEL_SIZE = 3

# Start the camera capture
cap = cv2.VideoCapture(0)

# Give it a few seconds for the camera to normalize
#  and me to get out of the way.
print("starting in:")
for i in range(1, 3):
    print(f"{i} ...")
    time.sleep(1.0)
print("go!")

# Read one image of the background, which we'll use to
#  replace into the live image where we recognize red.
ret, background_image = cap.read()

# Flip the image so that it displays like a mirror
#  This is a lot more intuitive if you're playing around
#  in front of the screen
background_image = cv2.flip(background_image, 1)

# Display the background image in a separate window for reference
cv2.imshow(BACKGROUND_WINDOW_NAME, background_image)
cv2.waitKey(1)

# Set up a video writer to record the fun we're having
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(f'/tmp/images/cloak_vid_{datetime.now()}.avi', fourcc, 10.0, (640, 480))


# We'll use these timers for when to take an image
nowtime = time.clock()  # for the stills
vidtime = time.clock()  # for the video

while True:
    # Only keep the most recent text on the display.
    #  Comment out if you want to log a stream of stdout
    #  to a file.
    os.system('clear')

    # Capture an image in our "frame"
    ret, frame = cap.read()

    # Flip the image so that it displays like a mirror
    #  This is a lot more intuitive if you're playing around
    #  in front of the screen
    frame = cv2.flip(frame, 1)

    # Make a copy of the image in HSV space, where it's
    #  easy to recognize colors by filtering on the hue
    #  (the "H" in HSV)
    image_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Find the mask for where it's red
    # Where do we recognize bright red
    recognition_mask = cv2.inRange(
        image_hsv,
        np.array([160, 150, 70]),
        np.array([180, 255, 255]))

    # Where do we recognize dark red
    recognition_mask_other = cv2.inRange(
        image_hsv,
        np.array([0, 180, 70]),
        np.array([20, 255, 255]))

    # Combine these two binary masks together
    recognition_mask += recognition_mask_other

    # Get rid of speckles on the recognition field
    recognition_mask = cv2.medianBlur(
        recognition_mask,
        DESPECKLE_KERNEL_SIZE)

    # Find indices where we want to replace the pixels
    recognition_indices = np.where(recognition_mask > 0)

    # Now, perform magic:
    #  At the indices where we recognized red, replace the
    #  background image pixel into the live image.
    #  Obviously, this assumes that these images are perfectly
    #  overlaid, which means the camera must remain still from
    #  the time you take the background picture on.
    frame[recognition_indices] = background_image[recognition_indices]

    # Write out a still image to a jpg in /tmp/images every N seconds
    if (time.clock() - nowtime) >= PHOTO_INTERVAL:
        cv2.imwrite(f"/tmp/images/cloak_{datetime.now()}.jpg", frame)
        nowtime = time.clock()

    # Write video frames to a file at about 10 Hz
    if (time.clock() - vidtime) >= 0.1:
        out.write(frame)
        vidtime = time.clock()

    print(datetime.now())
    print(f"last image captured on: {nowtime}: {datetime.now()}")
    print(f"now it is: {time.clock()}")

    # Display the altered image in a window.
    cv2.imshow(LIVE_WINDOW_NAME, frame)
    cv2.waitKey(1)



cap.release()
cv2.destroyAllWindows()

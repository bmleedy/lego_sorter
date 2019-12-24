#!/bin/python3

# Camera docs: https://picamera.readthedocs.io/en/release-1.13/api_camera.html#piresolution
# things I can set myself, AWB, Brightness, crop, exposure_mode, exposure_speed,iso (sensitivity), overlays, preview_alpha, preview_window, saturation, shutter_speed, 
# thought for future enhancement: at start time, calibrate against a background image.  Possibly only evaluate pixels which deviate significantly in hue from the original background image.

import numpy as np


import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import time
from datetime import datetime
 
# constants for tweaking
WINDOW_NAME = "Recognition"
SCALE_PERCENT = 20
PIXEL_THRESHOLD = 500
RANGE_PADDING = 20
SHOW_OVERLAY = True

# Setup the display window
if(SHOW_OVERLAY):
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 800,800)

# Use data to find bounds for detecting colors
def find_sane_bounds(data, range_padding = RANGE_PADDING):
    lower = data[0].copy()
    upper = data[0].copy()
    for hsvpoint in data:
        # print(f"--Range found: {lower} | {upper} | {hsvpoint}")
        for i in range(3):
            if((hsvpoint[i]+range_padding)  > upper[i]):
                # print(f"{hsvpoint[i]} is greater than {upper[i]}")
                upper[i] = hsvpoint[i]+range_padding
            if((hsvpoint[i]-range_padding) < lower[i]):
                # print(f"{hsvpoint[i]} is less than {lower[i]}")
                lower[i] = hsvpoint[i]-range_padding
    # print(f"Range found: {lower} | {upper}  (padded by {range_padding})")
    return lower,upper

# HSV's
# BROWN
brown_data = [
        [  9,  56,  32],
        [ 12,  47,  45],
        [  7,  63,  31],
        [ 10,  45,  49],
        [  9,  67,  24],
        [ 10,  50,  40]
        ]
# print("Brown")
brown_lower, brown_upper = find_sane_bounds(brown_data)

# RED
red_data = [
        # h    s    v
        [178, 169, 137], # top left
        [179, 135, 168], # top right
        [177, 160, 143], # middle
        [179, 178, 122], # bottom left
        [179, 165, 142], # bottom right
        ]
# print("Red")
red_lower, red_upper = find_sane_bounds(red_data)

# YELLOW
yellow_data = [
        # h    s    v
        [ 19, 151, 194], # top left
        [ 20, 128, 220], # top right
        [ 20, 140, 208], # middle
        [ 17, 171, 149], # bottom left
        [ 20, 139, 207], # bottom right
        ]
# print("Yellow")
yellow_lower, yellow_upper = find_sane_bounds(yellow_data)

# this is a constant for now, but todo: we should
# pick a spot on the belt that won't have any pieces 
# ever and use that to calibrate the belt color recognition 
belt_data = [
        # h    s    v
        [ 11, 90, 48],  # top left
        [  3, 53, 96],  # top right
        [ 13,115, 20],  # center left
        [  2, 55, 70],  # center right
        [ 20,191,  4],  # bottom left
        [  5, 85, 36]   # bottom right
    ]
# print("belt")
find_sane_bounds(belt_data)

# Run the camera
with PiCamera(
        camera_num=0,                # default
        stereo_mode='none',          # default
        stereo_decimate=False,       # default
        resolution = (160,96),       # default (10% of full resolution of 1600x900)
        framerate = 10,              # 10 fps, default is 30
        sensor_mode = 5) as camera:  # default=1, 5 is full FOV with 2x2 binning
    camera.awb_mode = 'off'          # turn off AWB because I will control lighting
    camera.awb_gains = 1.1           # Set constant AWB (tuple for red and blue, or constant)
    print("Camera setup complete.")

    # Setup the buffer into which we'll capture the images
    cam_image = PiRGBArray(camera)

    # start the preview window in the top left corner
    camera.start_preview(resolution=(160,96),window=(100,100,320,192), fullscreen=False)
    camera.preview_alpha = 150
    print("Camera preview started")

    # continuously capture files
    last_loop_time = time.time()
    for i, filename in enumerate(camera.capture_continuous(
                               cam_image,
                               format='bgr',
                               use_video_port=True, # faster, but less good images
                               resize = None         # resolution was specified above
                               )): 

        # load the image
        image = cam_image.array.copy()
        image_hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)


        # Super simple approach:
        #
        # inside a specific box, count the number of pixels I think are each color 
        red_mask = cv2.inRange(image_hsv, np.array(red_lower), np.array(red_upper))
        brown_mask = cv2.inRange(image_hsv, np.array(brown_lower), np.array(brown_upper))
        yellow_mask = cv2.inRange(image_hsv, np.array(yellow_lower), np.array(yellow_upper))

        # find where the masks found the colors
        red_indices = np.where(red_mask > 0)
        yellow_indices = np.where(yellow_mask > 0)
        brown_indices = np.where(brown_mask > 0)

        # todo: we should be able to filter out less-contiguous pixels (this would be a particle filter?)
        red_pixels = red_indices[0].size
        yellow_pixels = yellow_indices[0].size
        brown_pixels = brown_indices[0].size
        all_pixel_counts = [red_pixels, yellow_pixels, brown_pixels]
        print(f"Pixel counts: red: {red_indices[0].size} yellow: {yellow_indices[0].size} brown: {brown_indices[0].size}")

        # If the total number of non-background pixels are below a certain threshold
        #  do nothing

        # If the total number of non-background pixels are above a certain threshold
        #  I think I have a part, so pick the part's color based on the dominant color 
        #  I see.  This should help when I have multi-colored parts.
        if(sum(all_pixel_counts) > PIXEL_THRESHOLD):
            if(red_pixels == max(all_pixel_counts)):
                print("RED RECOGNIZED!")
            elif(yellow_pixels == max(all_pixel_counts)):
                print("YELLOW RECOGNIZED!")
            elif(brown_pixels == max(all_pixel_counts)):
                print("BROWN RECOGNIZED!")
            else:
                print("RECOGNITION FAILURE :_(")
        if(SHOW_OVERLAY):
            image[red_indices[0], red_indices[1], :] = [0,0,255]
            image[yellow_indices[0], yellow_indices[1], :] = [0,255,255]
            image[brown_indices[0], brown_indices[1], :] = [0,25,51]
            cv2.imshow(WINDOW_NAME, image)
            cv2.waitKey(1)


        # display the loop speed
        now_time=int(round(time.time() * 1000))
        print(f"{datetime.now()} : Loop [{i}] completed in {now_time-last_loop_time}ms")
        last_loop_time =now_time

        # clear the buffers for the image
        cam_image.truncate(0)
    camera.stop_preview()

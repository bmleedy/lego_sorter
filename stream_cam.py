#!/bin/python3

# Camera docs: https://picamera.readthedocs.io/en/release-1.13/api_camera.html#piresolution
# things I can set myself, AWB, Brightness, crop, exposure_mode, exposure_speed,iso (sensitivity), overlays, preview_alpha, preview_window, saturation, shutter_speed, 
# thought for future enhancement: at start time, calibrate against a background image.  Possibly only evaluate pixels which deviate significantly in hue from the original background image.

import numpy as np

# Camera Imports
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import time
from datetime import datetime
import os

# GPIO Imports
import RPi.GPIO as GPIO

# constants for tweaking
WINDOW_NAME = "Recognition"
SCALE_PERCENT = 20
PIXEL_THRESHOLD = 50
RANGE_PADDING = 10
SHOW_OVERLAY = True
COLOR_COLUMN_WIDTH=10

# setup GPIO (https://pythonhosted.org/RPIO/)
VALVE_PIN=18
GPIO.setmode(GPIO.BCM)
GPIO.setup(VALVE_PIN, GPIO.OUT)
GPIO.output(VALVE_PIN, GPIO.HIGH)


# Detection box location
XMIN=16
XMAX=85
YMIN=96
YMAX=121
SHOW_BOX=True


class Lego:
    name="undefined"
    upper_hsv=[0, 0, 0]
    lower_hsv=[0, 0, 0]
    display_bgr=[0,0,0]
    recognition_mask=[]
    recognition_indices=[]
    pixel_count=0
    jet_number=-1  #default to no jet assigned
    
    def __init__(self, name, lowerhsv, upperhsv, display_color):
        self.name = name
        self.upper_hsv = upperhsv
        self.lower_hsv = lowerhsv
        self.display_bgr = display_color


    def recognize_at(self, image, minpoint, maxpoint):
        print(self.name)
        # Super simple approach:
        # inside a specific box, count the number of pixels I think are each color 
        self.recognition_mask = cv2.inRange(
            image, 
            np.array(self.lower_hsv), 
            np.array(self.upper_hsv))

        # find where the masks found the colors
        # (making a trade-off here because I'm doing recognition on the whole image, 
        #    then only paring down here)
        self.recognition_indices = np.where(
                self.recognition_mask[minpoint[0]:maxpoint[0], # XMIN:XMAX 
                    minpoint[1]:maxpoint[1]] > 0) # YMIN: YMAX

        # todo: we should be able to filter out less-contiguous pixels (this would be a particle filter?)
        self.pixel_count = self.recognition_indices[0].size
        print(self.pixel_count)

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

# Define things we want to recognize

legos = []
#Brown
legos.append(
        Lego(
            'brown',
            [  0, 140, 140], # lower HSV
            [ 10, 255, 255], # upper HSV
            (0, 25, 51)      # display color
            )
        )

# RED
legos.append(
        Lego(
            'red',
            [169,  90, 140], # force low
            [199, 255, 255], # force high 
            (0, 0, 255)      # bgr display color
            )
        )
# YELLOW
legos.append(
        Lego(
            'yellow',
            [ 10,  30, 140], # force low
            [ 35, 240, 255], # force high 
            (0,255,255)      # bgr display color
            )
        )

# GREEN
legos.append(
        Lego(
            'green',
            [ 50,  30, 140], # force low
            [ 77, 255, 255], # force high 
            (0,255,0)        # bgr display color
            )
        )
# WHITE
legos.append(
        Lego(
            'white',
            [ 0,  0, 150],  # force low
            [ 255, 10, 255], # force high 
            (255,255,255)   # bgr display color
            )
        )

# Run the camera
with PiCamera(
        camera_num=0,                # default
        stereo_mode='none',          # default
        stereo_decimate=False,       # default
        resolution = (160,96),       # default (10% of full resolution of 1600x900)
        framerate = 10,              # 10 fps, default is 30
        sensor_mode = 5) as camera:  # default=1, 5 is full FOV with 2x2 binning
    #camera.awb_mode = 'off'          # turn off AWB because I will control lighting
    camera.awb_gains = (1.184,2.969) # Set constant AWB (tuple for red and blue, or constant)
    # time.sleep(2)
    print("{datetime.now()} Camera setup complete.")
    print(f"{datetime.now()} AWB Gains are {camera.awb_gains}")
    # time.sleep(3)

    # Setup the buffer into which we'll capture the images
    cam_image = PiRGBArray(camera)

    # start the preview window in the top left corner
    camera.start_preview(resolution=(160,96),window=(40,40,320,192), fullscreen=False)
    camera.preview_alpha = 200
    print("{datetime.now()} Camera preview started")

    # continuously capture files
    last_loop_time = time.time()
    for i, filename in enumerate(camera.capture_continuous(
                               cam_image,
                               format='bgr',
                               use_video_port=True, # faster, but less good images
                               resize = None         # resolution was specified above
                               )): 

        # clear the screen
        os.system('clear')

        # load the image
        image = cam_image.array.copy()
        image_hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)


        # Run recognition on the same image for each lego type
        for lego in legos:
            lego.recognize_at(image, (XMIN,YMIN), (XMAX,YMAX))

        all_pixel_counts = 0
        for lego in legos:
            all_pixel_counts += lego.pixel_count

        print(f"{datetime.now()} {all_pixel_counts} Pixels detected")
        print_string=""
        for lego in legos:
            print_string += f"{lego.name:^{COLOR_COLUMN_WIDTH}}|"
        print(print_string)
        print_string=""
        for lego in legos:
            print_string += f"{lego.pixel_count:^{COLOR_COLUMN_WIDTH}}|"
        print(print_string)


        # If the total number of non-background pixels are below a certain threshold
        #  do nothing

        # If the total number of non-background pixels are above a certain threshold
        #  I think I have a part, so pick the part's color based on the dominant color 
        #  I see.  This should help when I have multi-colored parts.
        if(all_pixel_counts > PIXEL_THRESHOLD):
            GPIO.output(VALVE_PIN, GPIO.LOW)
            max_pixels = 0
            detection_name = ""
            for lego in legos:
                if lego.pixel_count > max_pixels:
                    max_pixels = lego.pixel_count
                    detection_name = lego.name
            print(f"{lego.name} RECOGNIZED!")
        else:
            GPIO.output(VALVE_PIN, GPIO.HIGH)


        if(SHOW_BOX):
            cv2.rectangle(image, (YMIN, XMIN), (YMAX, XMAX), (0,255,0), 1)

        if(SHOW_OVERLAY):
            for lego in legos:
                image[lego.recognition_indices[0]+XMIN, lego.recognition_indices[1]+YMIN] = lego.display_bgr
            cv2.imshow(WINDOW_NAME, image)
            cv2.waitKey(1)

        # display the loop speed
        now_time=int(round(time.time() * 1000))
        print(f"Loop [{i}] completed in {now_time-last_loop_time}ms")
        last_loop_time =now_time

        # clear the buffers for the image
        cam_image.truncate(0)
    camera.stop_preview()

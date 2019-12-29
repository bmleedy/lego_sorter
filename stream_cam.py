#!/bin/python3

# Camera docs: https://picamera.readthedocs.io/en/release-1.13/api_camera.html#piresolution
# things I can set myself, AWB, Brightness, crop, exposure_mode, exposure_speed,iso (sensitivity), overlays, preview_alpha, preview_window, saturation, shutter_speed, 
# thought for future enhancement: at start time, calibrate against a background image.  Possibly only evaluate pixels which deviate significantly in hue from the original background image.
# Thoughts on controlling the air valves:
#  I'm going to take the simple approach first, and hopefully it's sufficient:
#    1. Detect different colors in zones in front of their respective valves
#    2. If enough of the first color is detected, puff it into that color's bin
#    3. Otherwise, let it ride through as many detection zones as necessary until it's detected or falls off the track
#  Upsides:
#    1. It's dead simple and reactive.  No state needed to manage
#    2. No timing tuning needed for detect-then-wait method (source of failure)
#    3. No tracking needed (source of failure/flakiness)
#    4. Less memory/CPU intensive
#
#  Downsides:
#    1. A multi-color part could slip past without enough "density" of any one color
#    2. More detection zones means more potential variation in the lighting - same part could look yellow in one zone and orange in the next, causing misses

import numpy as np

# Camera Imports
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import time
from datetime import datetime
import os
# todo: lintme

# GPIO Imports
import RPi.GPIO as GPIO

# constants for tweaking
WINDOW_NAME = "Recognition"
SCALE_PERCENT = 20
PIXEL_THRESHOLD = 50
RANGE_PADDING = 10
SHOW_OVERLAY = True
COLOR_COLUMN_WIDTH=10
OUTPUT_VIDEO = False
VIDEO_NAME = "output.avi"

# setup GPIO (https://pythonhosted.org/RPIO/)
VALVE_PIN=18
GPIO.setmode(GPIO.BCM)
GPIO.setup(VALVE_PIN, GPIO.OUT)
GPIO.output(VALVE_PIN, GPIO.HIGH)


# Detection box location
XMIN=36
XMAX=85
YMIN=96
YMAX=121
SHOW_BOX=True

# todo: fork data to a logfile in /var

class Lego:
    name="undefined"
    upper_hsv=[0, 0, 0]
    lower_hsv=[0, 0, 0]
    display_bgr=[0,0,0]
    recognition_mask=[]
    recognition_indices=[]
    pixel_count=0
    jet_number=-1  #default to no jet assigned
    recognition_box = [(0, 0), (0, 0)]  # (XMIN,YMIN),(XMAX,YMAX)
    
    def __init__(self, name, lowerhsv, upperhsv, display_bgr, recognition_box, jet_number=0):
        self.name = name
        self.upper_hsv = upperhsv
        self.lower_hsv = lowerhsv
        self.display_bgr = display_bgr
        self.recognition_box = recognition_box
        self.jet_number = jet_number

    def recognize_at(self, image, box=None):
        if (box == None):
            box=self.recognition_box

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
                self.recognition_mask[box[0][0]:box[1][0], # XMIN:XMAX 
                    box[0][1]:box[1][1]] > 0) # YMIN: YMAX

        # todo: we should be able to filter out less-contiguous pixels (this would be a particle filter?)
        self.pixel_count = self.recognition_indices[0].size
        # print(f"{self.name} found {self.pixel_count}")

# Setup the display window
if(SHOW_OVERLAY):
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 800,800)

# Define legos we want to recognize
# todo: move lego configurations over to a json file, or separate module
legos = []
#Brown
legos.append(
        Lego(
            name='brown',
            lowerhsv=[  0, 140, 140], # lower HSV threshold
            upperhsv=[ 10, 255, 255], # upper HSV threshold
            display_bgr=(0, 25, 51),   # display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            )
        )

# RED
legos.append(
        Lego(
            name='red',
            lowerhsv=[169,  90, 140],  # lower HSV threshold
            upperhsv=[199, 255, 255],  # upper HSV threshold
            display_bgr=(0, 0, 255),    # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            )
        )
# YELLOW
legos.append(
        Lego(
            name='yellow',
            lowerhsv=[ 28,  75, 140], # force low
            upperhsv=[ 35, 240, 255], # force high 
            display_bgr=(0,255,255),      # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            
            )
        )
# Orange 
legos.append(
        Lego(
            name='orange',
            lowerhsv=[ 15,  75, 140], # force low
            upperhsv=[ 27, 240, 255], # force high 
            display_bgr=(0,165,255),      # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            )
        )

# GREEN
legos.append(
        Lego(
            name='green',
            lowerhsv=[ 60,  50, 100], # force low
            upperhsv=[ 75, 255, 255], # force high 
            display_bgr=(0,255,0),        # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            )
        )
# WHITE
legos.append(
        Lego(
            name='white',
            lowerhsv=[   0,  0, 150],  # force low
            upperhsv=[ 255, 10, 255], # force high 
            display_bgr=(255,255,255),   # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            )
        )
# Blue
legos.append(
        Lego(
            name='blue',
            lowerhsv=[ 93,  30, 100],  # force low
            upperhsv=[103, 255, 255], # force high 
            display_bgr=(255,0,0),   # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
            )
        )

# Grey
legos.append(
        Lego(
            name='grey',
            lowerhsv=[  0,  11, 150],  # force low
            upperhsv=[255,  50, 255], # force high 
            display_bgr=(200, 200, 200),   # bgr display color
            recognition_box=[ (XMIN,YMIN),(XMAX,YMAX) ],
            jet_number = 0
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

    if(OUTPUT_VIDEO):
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 10.0, (160,96))

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
            lego.recognize_at(image_hsv)

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
        detection_name = ""
        detection_color= (0,0,0)
        if(all_pixel_counts > PIXEL_THRESHOLD):
            GPIO.output(VALVE_PIN, GPIO.LOW)
            max_pixels = 0
            for lego in legos:
                if lego.pixel_count > max_pixels:
                    max_pixels = lego.pixel_count
                    detection_name = lego.name
                    detection_color= lego.display_bgr
            print(f"{detection_name} RECOGNIZED! {max_pixels} pixels")
        else:
            GPIO.output(VALVE_PIN, GPIO.HIGH)

        if(SHOW_BOX):
            cv2.rectangle(image, (YMIN, XMIN), (YMAX, XMAX), (0,0,0), 1)

        if(SHOW_OVERLAY):
            for lego in legos:
                image[lego.recognition_indices[0]+XMIN, lego.recognition_indices[1]+YMIN] = lego.display_bgr
          #  if(detection_name != ""):
            cv2.putText(image, f"{detection_name}", (2, 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,  # size multiplier
                    detection_color,
                    1,     # thickness
                    False)
            cv2.waitKey(1)
            cv2.imshow(WINDOW_NAME, image)

        if(OUTPUT_VIDEO):
            out.write(image)
        # display the loop speed
        now_time=int(round(time.time() * 1000))
        print(f"Loop [{i}] completed in {now_time-last_loop_time}ms")
        last_loop_time =now_time

        # clear the buffers for the image
        cam_image.truncate(0)
    camera.stop_preview()
    out.release()
    cv2.destroyAllWindows()

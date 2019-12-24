# import the necessary packages
import numpy as np
# import argparse
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import time
 
# construct the argument parse and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--image", help = "path to the image")
# args = vars(ap.parse_args())


# todo: downsample image a lot to reduce work

WINDOW_NAME = "Recognition"
SCALE_PERCENT = 20
PIXEL_THRESHOLD = 500

# draw the box we're examining on the image
# cv2.rectangle(raw_image, (1336, 650), (2328,1500), (0,255,0), 4)
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, 800,800)

camera=PiCamera()
cam_image = PiRGBArray(camera)
camera.start_preview()
time.sleep(2)

while(True):

    # load the image
    #raw_image = cv2.imread("brown.jpg")
    camera.capture(cam_image,format="bgr")
    raw_image = cam_image.array

    # crop the image
    cropped_image = raw_image[650:1500, 1336:2328]
    del(raw_image) # save memory
    #cv2.imshow("cropped",image_cropped)
    new_width = int(cropped_image.shape[1] * SCALE_PERCENT / 100)
    new_height = int(cropped_image.shape[0] * SCALE_PERCENT / 100)
    dimensions = (new_width, new_height)
    resized_image = cv2.resize(cropped_image, dimensions, interpolation = cv2.INTER_LINEAR)
    del(cropped_image) # save memory
    # todo: INTER_NEAREST might be faster?
    print(f"resized image size is now {resized_image.shape}")
    image = resized_image

    image_hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)


    def find_sane_bounds(data, range_padding = 2):
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
        print(f"Range found: {lower} | {upper}  (padded by {range_padding})")
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
    print("Brown")
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
    print("Red")
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

    print("Yellow")
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
    print("belt")
    find_sane_bounds(belt_data)



    # Super simple approach:
    #
    # inside a specific box, count the number of pixels I think are each color 
    red_mask = cv2.inRange(image_hsv, np.array(red_lower), np.array(red_upper))
    brown_mask = cv2.inRange(image_hsv, np.array(brown_lower), np.array(brown_upper))
    yellow_mask = cv2.inRange(image_hsv, np.array(yellow_lower), np.array(yellow_upper))

    # draw the masks being applied
    red_indices = np.where(red_mask > 0)
    image[red_indices[0], red_indices[1], :] = [0,0,255]
    yellow_indices = np.where(yellow_mask > 0)
    image[yellow_indices[0], yellow_indices[1], :] = [0,255,255]
    brown_indices = np.where(brown_mask > 0)
    image[brown_indices[0], brown_indices[1], :] = [0,25,51]

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


    # thought for future enhancement: at start time, calibrate against a background image.  Possibly only evaluate pixels which deviate significantly in hue from the original background image.

    cv2.imshow(WINDOW_NAME, image)
    # cv2.waitKey()

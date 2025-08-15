"""
OUTDATED CODE FOR INITAL DETECTION MODEL
"""

import cv2 
import numpy as np 
video_path = "test_vid.mov"

point = (1243,1037)
radius = 10 
threshold = 15 
frame_count = 0
last_trigger = -15
timestamps = [] 
cap = cv2.VideoCapture(video_path)

ret,prev_frame = cap.read()

prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY) # turn the prev frame into gray

while cap.isOpened():
    ret,frame = cap.read() 
    if not ret:
        break 
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    frame_count +=1 
    # gray 
    # now we need to crop it so it fits 
    x,y = point 
    # 
    cropped_gray = gray[y-radius:y+radius, x-radius:x+radius]
    cropped_prev_gray = prev_gray[y-radius:y+radius, x-radius:x+radius]
    if cropped_prev_gray.shape == cropped_gray.shape:
        difference = np.abs(cropped_gray-cropped_prev_gray)
        average = np.mean(difference)
        if average > threshold and (frame_count - last_trigger) > threshold:
            time_passed = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            timestamps.append(time_passed)
            last_trigger= frame_count 
    prev_gray = gray


# Convert to grayscale for pixel comparison

# cap = cv2.VideoCapture(video_path)
# ret,prev_frame= cap.read()

# prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY) # cv2 color changes ti to greyscale, we need this because prev gray is called in our function to check prev

# while cap.isOpened(): # why the capture is open, because we dont need to actually shwo the video on screen 
#     ret, frame = cap.read() # read the capture 
#     if not ret: #if no ret, break 
#         break

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # colour the frame greyscale 
#     # this would be a 
#     frame_count += 1 # increase the frame by 1 

#     x1,y1 = hoop_point_1
#     x2,y2 = hoop_point_2 
#     x = int((x1+x2)/2) 
#     y = int((y1+y2)/2) 
#     # the list splicing used here is how numpy array slicing works, grab those columns and rows only 

#     patch_prev = prev_gray[y-radius:y+radius, x-radius:x+radius] # the colour at the previous cap 
#     patch_now  = gray[y-radius:y+radius, x-radius:x+radius] # find the current gray 
#     """
#     turns this :
#     prev_gray = np.array([
#     [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9],
#     [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
#     [20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
#     [30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
#     [40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
#     [50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
#     [60, 61, 62, 63, 64, 65, 66, 67, 68, 69],
#     [70, 71, 72, 73, 74, 75, 76, 77, 78, 79],
#     [80, 81, 82, 83, 84, 85, 86, 87, 88, 89],
#     [90, 91, 92, 93, 94, 95, 96, 97, 98, 99],
# ])
#     into:
#     patch_prev = np.array([
#     [22, 23, 24, 25],
#     [32, 33, 34, 35],
#     [42, 43, 44, 45],
#     [52, 53, 54, 55]
# ])

# """
#     if patch_prev.shape == patch_now.shape: # safety check to see if they are the same dimensions, this might break if the pixel i picked was too close to the wrong side 
#         diff = np.abs(patch_now.astype(int) - patch_prev.astype(int))  #so we subtract two np arrays from each other and get a new array, the difference array 
#         mean_diff = np.mean(diff) # averages the change in pixel count from everything 

#         if mean_diff > threshold : # we need to make sure it can trigger on frame 1
            
#             # we need to make sure the frame_count we are getting the last one that occured, shots that are bouncing around the rim etc are allowed, but it will update the last seen occurnece
#             timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0  # how many milliseconds we are in the video, cap.get is needed to retrieve it, this is like telling cap hey i want you to get 0, and cap.get knows 0 means the time passed and 1 means fps etc 
#             print(f"Change detected at {timestamp:.2f}s") # converts timestamp,to 2 dp basically w an f string 
#             print(frame_count,last_trigger)
#             if (frame_count - last_trigger) < retrigger_threshold: # check inside loop to guarantee shots that are bouncing around are ok 
#                 if len(timestamps) > 0:
#                     timestamps[-1] = timestamp 
#                     last_trigger = frame_count 
#             else:
#                 timestamps.append(timestamp)
#                 last_trigger = frame_count # this way we dont count the next 15 frames 
#     prev_gray = gray # set the prev frame tot he current frame 
# cap.release()
# print("Timestamps of detected events:", timestamps)

# the format of timestamps looks like  [11.535, 27.135, 38.835] 
# we then need to actually crop the videos, use moviepy first, then switch to ffmpeg for optimisations


    

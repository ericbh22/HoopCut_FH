import cv2 
import numpy as np 
from moviepy.editor import *
from ultralytics import YOLO
import cv2
from collections import deque
import math 
import subprocess
import json
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt 
import os
# .\venv\Scripts\activate to enter venv
import platform
processing_progress = {} # global dictionary to be read from that is updated 

# class to store progress, and the keyword associated with it 
class ProgressTracker:
    "Class Description: Keeps track of the progress of the loading bar across different functions to allow for seamless loading experience"
    def __init__(self, session_id):
        self.session_id = session_id
        self.progress = 0
        self.stage = "Initializing"
        self.details = ""
        self.is_complete = False
        self.error = None
        
    def update(self, progress, stage, details=""):
        """
        Function Description: Updates the loading bar with progress, stage and details, where details is the text
        """
        self.progress = progress
        self.stage = stage
        self.details = details
        processing_progress[self.session_id] = {
            'progress': self.progress,
            'stage': self.stage,
            'details': self.details,
            'is_complete': self.is_complete,
            'error': self.error
        } # update the progress so it can be read globally 
        
    def complete(self):
        """
        Function Description: Completes the loading bar 
        """
        self.is_complete = True
        self.progress = 100
        self.stage = "Complete"
        processing_progress[self.session_id] = {
            'progress': self.progress,
            'stage': self.stage,
            'details': self.details,
            'is_complete': self.is_complete,
            'error': self.error
        }
        
    def error_occurred(self, error_message):
        """
        Function Description: displays an error on the loading bar 
        """
        self.error = error_message
        self.stage = "Error"
        processing_progress[self.session_id] = {
            'progress': self.progress,
            'stage': self.stage,
            'details': self.details,
            'is_complete': self.is_complete,
            'error': self.error
        }
    

def load_gpu():
    try:
        import torch 
        import ultralytics
        if torch.cuda.is_available():
            print("using GPU")
            model = YOLO("models/best.pt") 
            model.to("cuda")
        else:
            model = YOLO("models/best.pt") 
            model.to("cpu")
        return model 
    except ImportError as e:
        raise RuntimeError("YOLO or torch not installed. Please install them to run detection.") from e
    
# this is used to rotate the video 
def get_rotation_angle(video_path,ffprobe):
    try:
        cmd = [
            ffprobe, "-v", "error",
            "-print_format", "json",
            "-show_streams",
            video_path
        ]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        info = json.loads(output)
        for stream in info.get("streams", []):
            side_data = stream.get("side_data_list", [])
            for entry in side_data:
                if entry.get("rotation") is not None:
                    return int(entry["rotation"])
        return 0
    except Exception as e:
        print(f"Failed to detect rotation: {e}")
        return 0

def rewrite_video(input_path, output_path, rotation_degrees,ffmpeg):
    """
    Function Description: Rotates the video so OpenCV can read it
    Approach Description: Uses FFMPEG to rewrite the entire video, changing the metadata so OPENCV can accurately read rotation metadata. 
    """
    if os.path.exists(output_path):
        return
    cmd = [
            ffmpeg,
            "-i", input_path,
            "-metadata:s:v", "rotate=0",
            "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast",
            "-c:a", "copy", 
            output_path
        ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Processed video saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print("FFmpeg processing failed:", e)


def hoop_select(video_path,three_point_toggle):
    """
    Function Description: Displays a window allowing users to select the locations of the hoop in this order, front rim, backrim, three point line 
    """
    selected_point = []
    # (1243, 1037)
    scale_factor = 1.0
        # def click_event(event, x, y, flags, param): # this works for properly structured videos 
        #     if event == cv2.EVENT_LBUTTONDOWN: # if the left mouse button is clicked 
        #         if len(selected_point) >3:
        #             selected_point.clear() # clear the list which holds selected point
        #         selected_point.append([x, y]) 
        #         print(f"Clicked coordinates: ({selected_point[0][0],selected_point[0][1]})")

    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            orig_x = int(x / scale_factor)
            orig_y = int(y / scale_factor)
            if len(selected_point) > 3:
                selected_point.clear()
            if three_point_toggle:
                selected_point.append([orig_x, orig_y+10])
            else: 
                selected_point.append([orig_x, orig_y+10])
            print(f"Clicked coordinates on original: ({orig_x}, {orig_y})")

    def resize_keep_aspect(frame, max_height=720):
        global scale_factor
        h, w = frame.shape[:2]
        scale_factor = min(max_height / h, 1.0)  # don't upscale if smaller
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        resized = cv2.resize(frame, (new_w, new_h))
        return resized

    cap = cv2.VideoCapture(video_path) 
    # normally we do this in a while loop so it rapidly reads the next frame again and again 
    ret, frame = cap.read() 

    # frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE) # this is really dodgy cuz u clip might not be rotated 
    if not ret: # ret is a boolean value indicating if it failed or not 
        raise Exception("couldn't read video")
    # resized_frame = resize_keep_aspect(frame) # for some videos we need to do this 
    # resized_frame = frame 
    # cv2.namedWindow("Click on the hoop", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("Click on the hoop", cv2.WINDOW_NORMAL)
    # cv2.namedWindow('Click on the hoop', cv2.WINDOW_KEEPRATIO)
    cv2.imshow('Click on the hoop', frame)
    # cv2.resizeWindow('Click on the hoop', 600, 600)
    # cv2.imshow("Click on the hoop", resized_frame) # displays the frame in a window called clicko nthe hoop, we need to show it first to set the mouse callback 
    cv2.setMouseCallback("Click on the hoop",click_event) # click_event is the function, so on click, we will print the selected point 
    while True:
        cv2.imshow("Click on the hoop", frame) # keep showing the frame on true 
        if cv2.waitKey(1) & 0xFF == ord('q'): # 0xff is a bitmask used to extract the lowest 8 bits of the keycode returned by waitkey 
            break
    cap.release() # stops all capture 
    cv2.destroyAllWindows()

    if selected_point:
        print("Hoop coordinates:", selected_point)
    else:
        print("No point selected.")
    

    return selected_point




def plot_shot_enhanced(last10, aftershot10, hoop_x_1, hoop_x_2, hoop_y_1, hoop_y_2, timestamp,rad,three,totalbool,output_path):
    """
    Function Description: Plots the trajectory of the shot, including quadratic prediction and linear prediction. 
    """
    os.makedirs(output_path, exist_ok=True)
    plt.figure(figsize=(5, 8))
    # print(f"first_release x: {first_release[0]}, three_point_x: {three_point_x}, hoop_x: {hoop_x}, three: {three}")
    # Convert to x and y arrays
    last10_x = [point[0] for point in last10]
    last10_y = [point[1] for point in last10]
    after10_x = [point[0] for point in aftershot10]
    after10_y = [point[1] for point in aftershot10]

    # Plot ball path
    plt.scatter(last10_x, last10_y, c='blue', label='Before hoop')
    if after10_x:
        plt.scatter(after10_x, after10_y, c='red', label='After hoop')
        for i, (x, y) in enumerate(zip(after10_x, after10_y)):
            plt.text(x + 1, y, str(i + len(last10)), fontsize=8, color='red')

    # Fit and plot parabola from last10 (shot arc)
    x_vals = np.array(last10_x)
    y_vals = np.array(last10_y)
    coeffs = np.polyfit(x_vals, y_vals, deg=2)
    a, b, c = coeffs
    x_smooth = np.linspace(min(x_vals), hoop_x_2 + 30, 200)
    y_smooth = a * x_smooth**2 + b * x_smooth + c
    plt.plot(x_smooth, y_smooth, color='green', linestyle='--', label='Fitted Parabola')

    # Plot hoop as a horizontal line
    if not three:
        plt.plot([hoop_x_1 + rad, hoop_x_2 - rad], [hoop_y_1, hoop_y_2], c='black', linewidth=3, label='Hoop')
    else:
        plt.plot([hoop_x_1+rad*1.5, hoop_x_2 - rad*1.5], [hoop_y_1, hoop_y_2], c='black', linewidth=3, label='Hoop (Three)') # + rad is used on the leftmost point, - rad is used on the rightmost point 

    # Add predicted intersection from parabola
    hoop_mid_y = (hoop_y_1 + hoop_y_2) // 2
    d = c - hoop_mid_y
    discriminant = b**2 - 4 * a * d
    if discriminant >= 0:
        sqrt_disc = np.sqrt(discriminant)
        x1 = (-b + sqrt_disc) / (2 * a)
        x2 = (-b - sqrt_disc) / (2 * a)
        intersect_x = max(x1, x2)
        plt.scatter([intersect_x], [hoop_mid_y], c='lime', s=80, marker='x', label='Parabola Prediction')
    plt.text(10, 10, "THREE" if three else "MID", fontsize=14, color="purple", weight='bold')
    # Add predicted intersection from linear
    if after10_x: # again after10_x might not even exist so we make this check first for linear predictions 
        print(f"last 10 after 10 {last10,aftershot10}")
        if len(last10) > 0 and len(aftershot10) > 0:
            x1, y1 = last10_x[-1], last10_y[-1]
            x2, y2 = after10_x[0], after10_y[0]
            run = x2 - x1
            rise = y2 - y1
            print(f"run { run}")
            if run != 0:

                gradient = rise / run
                x_at_hoop_y = ((hoop_mid_y - y1) / gradient) + x1
                plt.scatter([x_at_hoop_y], [hoop_mid_y], c='orange', s=80, marker='^', label='Linear Prediction')
        
    # Final styling
    plt.gca().invert_yaxis()
    plt.title(f"Shot Trajectory - {timestamp:.2f}s")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.grid(True)
    if not totalbool:
        final_path = os.path.join(output_path, f"shot_{timestamp:.2f}s.png")
    else:
        final_path = os.path.join(output_path, f"shot_{timestamp:.2f}s_total.png")
    plt.savefig(final_path)
    plt.close()



def ball_intersect_parabola(last10,hoop_x_1,hoop_x_2,hoop_y_1, hoop_y_2,rad,first_release,three_point_line):
    """
    Function description: Calculates where the parabola will intersect the y value of where the hoop is 
    """
    # calculate hoop mid_x and hoop mid_y to use later in calculations for intersection to see if either is within range 
    # checks last 10 and all 
    if three_point_line:
        three_point_x , three_point_y = three_point_line
    hoop_mid_x = (hoop_x_1+hoop_x_2)//2
    hoop_mid_y = (hoop_y_1+hoop_y_2)//2
    last10_x = [point[0] for point in last10]
    last10_y = [point[1] for point in last10]
    x_vals = np.array(last10_x) # so we can do matrix maths 
    y_vals = np.array(last10_y)
    coeffs = np.polyfit(x_vals, y_vals, deg=2)  
    a, b, c = coeffs
    x_smooth = np.linspace(min(x_vals), hoop_x_2 + 30, 200) # these are purely used for plotting 
    # no nvm we wanna find the x value from the y value 

    def solve_parabola_y_to_x(a, b, c, y): # we have the y value, we need to know if it matches the x value of the hoop 
        # we need to take the positive x value
        d = c - y
        discriminant = b**2 - 4*a*d

        if discriminant < 0:
            return []  # no real solutions
        elif discriminant == 0:
            x = -b / (2*a)
            return [x]
        else:
            sqrt_disc = math.sqrt(discriminant)
            x1 = (-b + sqrt_disc) / (2*a)
            x2 = (-b - sqrt_disc) / (2*a)
            return [x1, x2]
    
    x_candidates = solve_parabola_y_to_x(a, b, c, hoop_mid_y)
    if not x_candidates: # in the case it returns a weird parabola ( Unlikely )
        return False
    positivex = max(x_candidates)
    if three_point_line and first_release[0] < three_point_x + rad*2:
        if hoop_x_1+(rad*1.5)<positivex<hoop_x_2-(rad*1.5):
            return True  
        else:
            return False
    else: 
        if hoop_x_1+rad<positivex<hoop_x_2-rad:
            return True  
        else:
            return False 
    
def ball_intersect_linear(last10,after10,hoop_x_1,hoop_x_2,hoop_y_1, hoop_y_2):
    """
    Function Description: Taking the last occurence above the ring and the first occurence under the ring, map a linear relation and determine if it intersects through the hoop
    """
    if not after10:
        return False # in case we do not have a detection 
    hoop_mid_x = (hoop_x_1+hoop_x_2)//2
    hoop_mid_y = (hoop_y_1+hoop_y_2)//2
    last10_x = [point[0] for point in last10]
    last10_y = [point[1] for point in last10]
    after10_x = [point[0] for point in after10]
    after10_y = [point[1] for point in after10]
    last_point_before = [last10_x[-1],last10_y[-1]]
    last_point_after = [after10_x[0],after10_y[0]]
    x1, y1 = last_point_before
    x2, y2 = last_point_after

    run = x2 - x1
    rise = y2 - y1
    print(f"run {run,x2,x1,y2,y1}")
    if run == 0:
        return hoop_x_1<=x1 <=hoop_x_2  # vertical line case
    
    gradient = rise / run

    # Solve for x given hoop y
    x_at_hoop_y = ((hoop_mid_y - y1) / gradient) + x1

    # Check if it lands within the hoop x-range
    within_hoop = hoop_x_1 <= x_at_hoop_y <= hoop_x_2

    return within_hoop

def find_hoop(video,three_point_toggle):
    """
    Function Description: Uses the hoop detection model to find the location of the hoop, and takes the top left and top right coordinates of the bounding box which represents front rim and back rim. 
    Lowers the y coordinates of the ring based on three_point_toggle, as the lower the ring is, the less chance a close shot is made (Experimental)
    """
    model = YOLO("models/hoop.pt")
    cap = cv2.VideoCapture(video)
    coordinates = [] 
    while cap.isOpened():
        ret,frame = cap.read() 
        if not ret:
            break 
        results = model(frame, imgsz=1280, conf=0.33)
        annotated_frame = results[0].plot() 
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            if label == "hoop":
                x1,y1,x2,y2 = box.xyxy[0]
                if three_point_toggle:
                    coordinates.append([int(x1),int(y1)+10])
                    coordinates.append([int(x2),int(y1)+10])
                else:
                    coordinates.append([int(x1),int(y1)+3])
                    coordinates.append([int(x2),int(y1)+3])
                cap.release()
                break 
    print(coordinates)
    return coordinates 



def detection_model(selected_point,video_path,plot_output_path,DEBUG_LOG_PATH,progress_tracker):
    """
    Function Description: Runs the model to find all instances of shot makes/misses, and stores them into two seperate arrays, a boolean array and an array of floats indicating time stamps
    """
    # frame tracking to try and figure out progress bar 
    # we meed to know total frames, and fps 
    
    hoop_point_1 = selected_point[0]
    hoop_point_2 = selected_point[1]
    if len(selected_point) ==3 :
        three_point_line = selected_point[2]
    else:
        three_point_line = None 
    model = load_gpu()
    cap = cv2.VideoCapture(video_path)
    last10= deque()  # we use a deque cuz we wanna get rid of the most recent one 
    totalshottracking = [] 
    aftershot10 = []
    frame_idx = 0
    make_miss = [] 
    timestamps_2 = [0] 
    crosstime = None 
    first_release = None 

    # fps and total frames calc
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames // fps 
    if progress_tracker:
        progress_tracker.update(5, "Loading AI model", f"Video: {duration:.1f}s, {total_frames} frames")
    while cap.isOpened():
        ret, frame = cap.read()
        basketballs_in_frame = [] 
        # frame = cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE) # why does the argument passed thru also need to be cv2.?
        frame_idx += 1
        if progress_tracker:
            if frame_idx % 30 == 0:
                    progress_percentage = 10 + (frame_idx / total_frames) * 75  # 10-85% for video processing
                    progress_tracker.update(
                        progress_percentage,
                        "Processing video",
                        f"Frame {frame_idx}/{total_frames} ({progress_percentage:.1f}%)"
                    )
        hoop_x_1, hoop_y_1 = hoop_point_1
        hoop_x_2, hoop_y_2 = hoop_point_2 
        if three_point_line:
            three_point_x , three_point_y = three_point_line
        hoop_x = (hoop_x_1+hoop_x_2) /2 
        hoop_y = (hoop_y_1+hoop_y_2)/2 
        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        mid = frame_width //2 
        # now we need to detect where the ball is at each point, so run YOLO model on this frame 
        # the x doesnt really matter YET due to the position of the shot, 
        # we really have to consider the start of the hoop and the end of the hoop, and if it goes through it. this means we either need to let user click on the those two points, or pray our model can detect it
        if not ret:
            break
        results = model(frame, imgsz=1280, conf=0.33)  # movign confidence up from 0.33 to 0.4 to remove some false detections 
        # draw da results 
        for box in results[0].boxes: # results is strucutred as 
            c_id = int(box.cls[0])
            label = model.names[c_id]
            if label == "Basketball":
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                rad = abs(x2 - x1) / 2
                centrex = int((x1 + x2) / 2)
                centrey = int((y1 + y2) / 2)
                basketballs_in_frame.append(([centrex, centrey], float(box.conf[0])))  # add confidence
        basketballs_in_frame.sort(key=lambda b: -b[1])  # highest confidence first
        # basketballs_in_frame.sort(key=lambda b: b[0][1]) #  best y value, different sort
        if basketballs_in_frame: # the issue here is multiple basketballs detected in one frame due to hands etc 
            basketballcentre = basketballs_in_frame[0][0]
            # x1, y1, x2, y2 = box.xyxy[0].tolist() # we need [0] because xyxy returns a tensor, w information abt gpu and stuff, if we want the actual x and y this is how we do it 
            # rad = abs(x2-x1)/2
            # centrex = int((x1+x2)/2) # becausew we dont wanna be using tensors 
            # centrey = int((y1+y2)/2)
            # basketballcentre = [centrex,centrey]
            basketballcentre = basketballs_in_frame[0][0]
            # print(f"centrex: {centrex}, centrey: {centrey}, hoop_y: {hoop_y}")
            if basketballcentre[1] < hoop_y: # 0,0 is the TOP LEFT of the screen 
                if first_release is None:
                    first_release = basketballcentre # use it to 
                if len(last10) < 10:
                    last10.append(basketballcentre)
                else:
                    last10.popleft()
                    last10.append(basketballcentre)
                annotated_frame = results[0].plot()
                save_folder = "./annotated_frames"
                os.makedirs(save_folder, exist_ok=True)
                cv2.imwrite(f"{save_folder}/preshot_{timestamp:.2f}.jpg", annotated_frame)
                # last10.append(basketballcentre)  #all this does is lower the accuract
                totalshottracking.append(basketballcentre)
                crosstime = timestamp  # this isnt really effective because sometimes the ball cuts out midair 
            else:
                # if hoop_y-200<=basketballcentre[1] <= hoop_y+200: #  so we are now definitely under the hoop but maybe using time is a better strategy
                if len(last10) >=1:
                    if len(last10)>=1 and timestamp - crosstime <=0.6 : # 1 second leeway between shot and next detection to prevent case where it swishes, we dont see it again, and then it comes back again, or situation where it bounces up and stuff 
                        # we need to make sure the after shot is SOMEWHAT close to get rid of bugs such as hand detection 
                        # now we wanna plot and somehow decide what to do 
                        annotated_frame = results[0].plot()
                        save_folder = "./annotated_frames"
                        os.makedirs(save_folder, exist_ok=True)
                        cv2.imwrite(f"{save_folder}/aftershot_{timestamp:.2f}.jpg", annotated_frame)
                        aftershot10.append(basketballcentre)
                        with open(DEBUG_LOG_PATH, "a") as f:
                            f.write(f"[timestamp: {timestamp:.2f}] Entered aftershot\n")
                            f.write(f"aftershot {aftershot10}, timestamp {timestamp}, crosstime {crosstime}, last10 {last10}\n")
                    elif len(last10)>=1 and timestamp - crosstime >0.6: # still verifying that we have a shot being put up 
                        with open(DEBUG_LOG_PATH, "a") as f:
                            f.write(f"[timestamp: {timestamp:.2f}] Entered plot logic block\n")
                            # f.write(f"first_release: {first_release}, three_point_x: {three_point_x}, rad: {rad}\n")
                            f.write(f"len(last10): {len(last10)}, len(aftershot10): {len(aftershot10)}\n")
                            f.write(f"aftershot {aftershot10}, timestamp {timestamp}, crosstime {crosstime}, last10 {last10}\n")
                        aftershot10.sort(key=lambda b:b[1])
                        # if hoop is on the right we check three pointer on left side 
                        # we need to get the x and y co ordinates and compare it to the middle 
                        
                        # if first_release[0] < three_point_x + rad*2:
                        #     plot_shot_enhanced(list(last10), aftershot10, hoop_x_1, hoop_x_2,hoop_y_1,hoop_y_2, timestamp,rad,True,False,plot_output_path)
                        #     plot_shot_enhanced(totalshottracking, aftershot10, hoop_x_1, hoop_x_2,hoop_y_1,hoop_y_2, timestamp,rad,True,True,plot_output_path)
                        # else:
                        plot_shot_enhanced(list(last10), aftershot10, hoop_x_1, hoop_x_2,hoop_y_1,hoop_y_2, timestamp,rad,False,False,plot_output_path)
                        plot_shot_enhanced(totalshottracking, aftershot10, hoop_x_1, hoop_x_2,hoop_y_1,hoop_y_2, timestamp,rad,False,True,plot_output_path)
                        # ok so we just need a boolean calculation, if either the parabola intersect the hoop or if the direct line from first and last intersect the hoop we can detect it as a "make"
                        if (ball_intersect_parabola(last10, hoop_x_1,hoop_x_2,hoop_y_1,hoop_y_2,rad,first_release,three_point_line) and ball_intersect_parabola(totalshottracking, hoop_x_1,hoop_x_2,hoop_y_1,hoop_y_2,rad,first_release,three_point_line)) or ball_intersect_linear(last10,aftershot10,hoop_x_1,hoop_x_2,hoop_y_1,hoop_y_2):
                            make_miss.append(True) # this is hinging on the fact our time detection and ai detection matches up, if one doesnt fire everything is going to be misalligned, so we might need to rethink this                        
                        else:
                            make_miss.append(False)
                        timestamps_2.append(timestamp) 
                        last10.clear()
                        aftershot10.clear()
                        first_release = None 
                        totalshottracking.clear()
                        basketballs_in_frame.clear()
    if progress_tracker:
        progress_tracker.update(85, "Video processing complete", "Preparing video clips...")
    return timestamps_2,make_miss



def save_clips(output_folder,timestamps,make_miss,video_path,ffmpeg,progress_tracker):
    """
    Function Description: Uses the timestamps folder to cut up the clips accordingly, and output them to folder of choice 
    """
    os.makedirs(output_folder, exist_ok=True)
    clip = VideoFileClip(video_path)
    padding_after = 1.0
    video_duration = clip.duration  # still use moviepy or cv2 to get this
    total_clips = len(timestamps) - 1
    for i in range(1, len(timestamps)):
        start = timestamps[i - 1]
        end = min(video_duration, timestamps[i] + padding_after)
        duration = end - start
        clip_progress = 90 + (i / total_clips) * 10
        if progress_tracker:
            progress_tracker.update(
                clip_progress,
                "Creating video clips",
                f"Processing clip {i}/{total_clips}"
            )
        # Output filename logic
        if i - 1 < len(make_miss):
            result = "make" if make_miss[i - 1] else "miss"
        else:
            result = "unknown"
        timestamp_str = f"{start:.2f}s"
        output_filename = f"{result}_{i}_{timestamp_str}.mp4"
        output_path = os.path.join(output_folder, output_filename)

        # ffmpeg command cuz its faster than moviepy
        cmd = [
            ffmpeg,
            "-ss", str(start),
            "-i", video_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-vf", (
                "zscale=t=linear:npl=100,"
                "format=gbrpf32le,"
                "zscale=p=bt709,"
                "tonemap=tonemap=hable:desat=0,"
                "zscale=t=bt709:m=bt709:r=tv,"
                "format=yuv420p"
            ),
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-c:a", "copy",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Saved: {output_filename}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing clip {i}: {e}")
    if progress_tracker:
        progress_tracker.complete()

def run_highlight_pipeline(video_path, output_dir="outputs/clips", plot_dir="outputs/plots"):
    ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    ffprobe_bin = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
    DEBUG_LOG_PATH = "loop_debug.txt"

    # Step 1: Fix rotation
    rotation = get_rotation_angle(video_path,ffprobe_bin)
    filename = os.path.basename(video_path)
    fixed_path = os.path.join("true_videos", filename)
    rewrite_video(video_path, fixed_path, rotation,ffmpeg_bin)

    # Step 2: Select hoop (can be skipped in Flask if coords are pre-defined or user inputs them elsewhere)
    selected_point = hoop_select(fixed_path,True)  # or predefine it with a UI in Flask

    # Step 3: Detect makes/misses
    timestamps, make_miss_array = detection_model(selected_point, fixed_path, plot_dir, DEBUG_LOG_PATH)

    # Step 4: Save clips
    save_clips(output_dir, timestamps, make_miss_array, fixed_path,ffmpeg_bin)

    return os.listdir(output_dir)  # So Flask can list downloadable clips

if __name__ == "__main__":
    ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    ffprobe_bin = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
    DEBUG_LOG_PATH = "loop_debug.txt"
    video_path = "./test_videos/DEMO_VID.mov"
    plot_folder = "./outputs/plots/ai_test_4"
    rotation = get_rotation_angle(video_path,ffprobe_bin) 
    filename = os.path.basename(video_path)
    output_path = os.path.join("./true_videos", filename)
    rewrite_video(video_path,output_path,rotation,ffmpeg_bin)
    video_path = output_path
    # selected_point = hoop_select(video_path,True)
    # print(f"manually selected point {selected_point}")
    selected_point = find_hoop(video_path,True)
    print(f"automatically selected point {selected_point}")
    timestamps, make_miss_array = detection_model(selected_point,video_path,plot_folder,DEBUG_LOG_PATH,None)
    output_folder = "./outputs/clips/ai_test_4"
    save_clips(output_folder,timestamps,make_miss_array,video_path,ffmpeg_bin,None)

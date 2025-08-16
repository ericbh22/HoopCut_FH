import os
import time
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, Response
from detector import run_highlight_pipeline, get_rotation_angle,rewrite_video,hoop_select,detection_model,save_clips, find_hoop 
import zipfile
from flask import send_file
import shutil
import platform
from config import auto_ai
import config 
from threading import Thread
from uuid import uuid4
from detector import ProgressTracker, processing_progress
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This will be 'main/'

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER_CLIPS = os.path.join(BASE_DIR, 'static', 'clips')
OUTPUT_FOLDER_PLOTS = os.path.join(BASE_DIR, 'static', 'plots')
OUTPUT_FOLDER_LOGS_DIR = os.path.join(BASE_DIR, 'static', 'logs')
OUTPUT_FOLDER_LOGS = os.path.join(OUTPUT_FOLDER_LOGS_DIR, "logs.txt")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_CLIPS, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_PLOTS, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_LOGS_DIR, exist_ok=True)



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER_CLIPS

def get_project_stats(project_name):
    """
    Function Description: Finds the project directory and goes through each video to tally up makes and misses
    Inputs: project_name : Str , the name of the project
    Outputs: Dictionary of makes, misses and total_vids 
    """
    print(f"project name{project_name}")
    projectroute = os.path.join(BASE_DIR,"projects", project_name,"clips")
    makes = 0 
    misses = 0 
    total_vids = 0 
    for name in os.listdir(projectroute):
        print(project_name,name)
        if "make" in name:
            makes +=1 
        else:
            misses+=1 
        total_vids +=1 
    return {"makes": makes, "misses": misses, "total_vids" : total_vids}

@app.route('/')
def home():
    return render_template('home.html')  # <-- this is now the landing page


@app.route("/index.html", methods=["GET", "POST"])
def index():
    project_root = os.path.join(BASE_DIR, 'projects')
    if request.method == "POST":
        video = request.files["video"]
        if video and video.filename.endswith((".mp4", ".mov")):
            ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg" #tracks operating system 
            ffprobe_bin = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
            filename = video.filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            project_name = f"{os.path.splitext(filename)[0]}_{timestamp}"
            project_path = os.path.join(BASE_DIR, 'projects', project_name)

            # Create project structure
            clips_path = os.path.join(project_path, 'clips')
            plots_path = os.path.join(project_path, 'plots')
            logs_path = os.path.join(project_path, 'logs.txt')
            os.makedirs(clips_path, exist_ok=True)
            os.makedirs(plots_path, exist_ok=True)

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            video.save(filepath)

            # Process
            rotation = get_rotation_angle(filepath,ffprobe_bin)
            rewrite_video(filepath, filepath, rotation,ffmpeg_bin)


            three_toggle = config.get_setting("three_point_adjust",True)
            if config.get_setting('auto_ai', True):
                try: 
                    selected_points = find_hoop(filepath,three_toggle)
                    if selected_points:
                        video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        project_path = os.path.join(BASE_DIR, 'projects', project_name)
                        clips_path = os.path.join(project_path, 'clips')
                        plots_path = os.path.join(project_path, 'plots')
                        logs_path = os.path.join(project_path, 'logs.txt')

                        os.makedirs(clips_path, exist_ok=True)
                        os.makedirs(plots_path, exist_ok=True)

                        # Debug: Print the validated points
                        print(f"Validated points: {selected_points}")
                        print(f"Video path: {video_path}")
                        print(f"Project path: {project_path}")

                        # Call detection model with validated points
                        timestamps, make_miss_array = detection_model(selected_points, video_path, plots_path, logs_path,None)
                        ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
                        save_clips(clips_path, timestamps, make_miss_array, video_path,ffmpeg_bin,None)

                        return redirect(url_for("project_view", project_name=project_name))
                    else:
                        print("Auto ai detection failed")
                        return redirect(url_for("select_hoop", project_name=project_name))
                except Exception as e:
                    print(f"Error in auto hoop detection: {e}")
                    # If auto detection fails, fall back to manual selection
                    return redirect(url_for("select_hoop", project_name=project_name))
            else:
                return redirect(url_for("select_hoop", project_name=project_name))
    
    # For GET request, get projects with stats
    if not os.path.exists(project_root):
        return render_template("index.html", projects=[])
    
    projects_with_stats = []
    project_names = [name for name in os.listdir(project_root) if os.path.isdir(os.path.join(project_root, name))]
    
    for project_name in project_names:
        if project_name is not None:
            stats = get_project_stats(project_name)
            projects_with_stats.append({
                'name': project_name,
                'makes': stats['makes'],
                'misses': stats['misses'],
                'total_vids': stats['total_vids']
            })
        
    return render_template("index.html", projects=projects_with_stats) 


@app.route("/projects/<project_name>") # any route that looks like projects/<project_name> should trigger project_view, at this point, extractthe project_name 
def project_view(project_name):
    base_path = os.path.join(BASE_DIR, 'projects', project_name)
    clips_path = os.path.join(base_path, 'clips')
    plots_path = os.path.join(base_path, 'plots')
    logs_path = os.path.join(base_path, 'logs.txt')

    clips = os.listdir(clips_path) if os.path.exists(clips_path) else []
    plots = os.listdir(plots_path) if os.path.exists(plots_path) else []
    log_content = ""
    if os.path.exists(logs_path):
        with open(logs_path, 'r') as f:
            log_content = f.read()

    return render_template("project_detail.html", project=project_name, clips=clips, plots=plots, logs=log_content)

@app.route("/projects/<project_name>/clips/<filename>")
def download_clip(project_name, filename):
    clip_path = os.path.join(BASE_DIR, 'projects', project_name, 'clips')
    return send_from_directory(clip_path, filename, as_attachment=True)

@app.route('/relabel', methods=['POST']) # used to relabel the videos and save them again 
def relabel_clip():
    data = request.get_json()
    filename = data.get("filename")
    new_label = data.get("newLabel")
    project_name = data.get("project")
    print(f"filename, project_name {filename,project_name,new_label}")

    clip_folder = os.path.join(BASE_DIR, 'projects', project_name, 'clips')
    old_path = os.path.join(clip_folder, filename)

    if not os.path.exists(old_path):
        return jsonify({"error": "File not found"}), 404

    if "make" in filename.lower():
        new_filename = filename.replace("make", "miss")
    elif "miss" in filename.lower():
        new_filename = filename.replace("miss", "make")
    else:
        return jsonify({"error": "Filename doesn't include make or miss"}), 400

    new_path = os.path.join(clip_folder, new_filename)
    os.rename(old_path, new_path)

    return jsonify({"success": True, "newFilename": new_filename})
@app.route("/download-all/<project>")
def download_all_clips(project):
    project_folder = os.path.join(BASE_DIR, "projects", project, "clips")
    print(project_folder)
    zip_path = os.path.join(BASE_DIR,"projects", project, f"{project}_clips.zip")
    print(zip_path)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    # Create zip file if it doesn't exist (optional: always recreate)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(project_folder):
            clip_path = os.path.join(project_folder, filename)
            zipf.write(clip_path, arcname=filename)

    return send_file(zip_path, as_attachment=True) # this is ourcreated path so we use send_file, when its user created, we use send from directory 
@app.route("/download-all-plots/<project>")
def download_all_plots(project):
    project_folder = os.path.join(BASE_DIR,"projects",project,"plots")
    print(f"project folder {project_folder}")
    zip_path = os.path.join(BASE_DIR,"projects",project,f"{project}_plots.zip")
    print(f"zip path {zip_path}")
    os.makedirs(os.path.dirname(zip_path),exist_ok=True )
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(project_folder):
            plot_path = os.path.join(project_folder,filename)
            zipf.write(plot_path,arcname = filename)
    return send_file(zip_path,as_attachment=True)

@app.route('/delete_project', methods=['POST'])
def delete_project():
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        
        if not project_name:
            return jsonify({'success': False, 'error': 'Project name is required'})
        
        # Define the path to the project directory
        # Adjust this path based on your project structure
        project_path = os.path.join(BASE_DIR, 'projects', project_name) 
        
        # Check if project exists
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': 'Project not found'})
        
        # Delete the project directory and all its contents
        shutil.rmtree(project_path)
        
        return jsonify({'success': True, 'message': f'Project "{project_name}" deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route("/select-hoop/<project_name>")
def select_hoop(project_name):
    project_path = os.path.join(BASE_DIR, 'projects', project_name)
    
    # Extract the original filename from the project name
    # project_name format: "originalfilename_timestamp"
    original_filename_part = project_name.rsplit('_', 1)[0]  # Get everything before the last underscore
    
    # Find the actual video file in uploads folder
    video_filename = None
    if os.path.exists(app.config["UPLOAD_FOLDER"]):
        for filename in os.listdir(app.config["UPLOAD_FOLDER"]):
            if filename.startswith(original_filename_part) and filename.endswith(('.mp4', '.mov')):
                video_filename = filename
                break
    
    if video_filename:
        video_url = url_for('uploaded_file', filename=video_filename)
        print(f"Video URL: {video_url}")
    else:
        video_url = None
        print("No video file found")
    
    return render_template("select_hoop.html", project_name=project_name, video_url=video_url)


@app.route("/submit-hoop/<project_name>", methods=["POST"])
def submit_hoop(project_name):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data received"}), 400
        
        points = data.get("points")  # This should be a list of 2 points
        
        if not points or len(points) < 2:
            return jsonify({"success": False, "error": "Exactly 2 points are required"}), 400

        # Validate and convert point data types
        validated_points = []
        try:
            for i, point in enumerate(points):
                if not isinstance(point, dict):
                    return jsonify({"success": False, "error": f"Point {i} must be an object with x,y coordinates"}), 400
                
                # Convert coordinates to float to ensure they're numbers
                x = point.get('x')
                y = point.get('y')
                
                if x is None or y is None:
                    return jsonify({"success": False, "error": f"Point {i} missing x or y coordinate"}), 400
                
                # Convert to float, handling strings
                try:
                    x = float(x)
                    y = float(y)
                except (ValueError, TypeError):
                    return jsonify({"success": False, "error": f"Point {i} coordinates must be numbers"}), 400
                
                validated_points.append([x,y])
                
        except Exception as point_error:
            return jsonify({"success": False, "error": f"Error validating points: {str(point_error)}"}), 400

        # Find the actual video file (same logic as select_hoop)
        original_filename_part = project_name.rsplit('_', 1)[0]
        video_filename = None
        
        if os.path.exists(app.config["UPLOAD_FOLDER"]):
            for filename in os.listdir(app.config["UPLOAD_FOLDER"]):
                if filename.startswith(original_filename_part) and filename.endswith(('.mp4', '.mov')):
                    video_filename = filename
                    break
        
        if not video_filename:
            return jsonify({"success": False, "error": "Video file not found"}), 404
        
        video_path = os.path.join(app.config["UPLOAD_FOLDER"], video_filename)
        project_path = os.path.join(BASE_DIR, "projects", project_name)
        clips_path = os.path.join(project_path, "clips")
        plots_path = os.path.join(project_path, "plots")
        logs_path = os.path.join(project_path, "logs.txt")
        os.makedirs(clips_path, exist_ok=True)
        os.makedirs(plots_path, exist_ok=True)

        session_id = str(uuid4())  # Generate unique session ID
        ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

        def background_task():
            try:
                tracker = ProgressTracker(session_id) # classes are used to pass instances through not copies
                tracker.update(0, "Initializing...")
                tracker.update(20, "Running manual detection...")

                timestamps, make_miss_array = detection_model(
                    validated_points, video_path, plots_path, logs_path, tracker)

                tracker.update(80, "Saving clips...")
                save_clips(clips_path, timestamps, make_miss_array, video_path, ffmpeg_bin, tracker)

                tracker.complete()
            except Exception as e:
                tracker.error_occurred(str(e))

        Thread(target=background_task).start()

        return jsonify({"session_id": session_id, "project_name": project_name}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500
    

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/toggle-auto-ai", methods=["POST"]) # turns on and off auto ai 
def toggle_ai():
    data = request.get_json()
    enabled = data.get("enabled", True)
    
    # Save the setting to persistent storage
    config.set_setting('auto_ai', enabled)
    
    # Also update the module variable for immediate use
    config.auto_ai = enabled
    
    return jsonify({"status": "ok", "auto_ai": enabled})
@app.route("/toggle-three",methods=["POST"]) # enabling three point adjust 
def toggle_three():
    data = request.get_json()
    enabled = data.get("enabled",False)

    config.set_setting("three_point_adjust", enabled)

    config.three_point_adjust = enabled 
    return jsonify({"status":"ok", "three_point_adjust":enabled})
# Add a route to get current settings (for loading initial state)
@app.route("/get-settings", methods=["GET"])
def get_settings():
    return jsonify({
        "auto_ai": config.get_setting('auto_ai', True),
        "three_point_adjust": config.get_setting("three_point_adjust",False)
    })

@app.route("/start-processing", methods=["POST"])
def start_processing():
    """
    Function Description: Starts the loading bar for tracking 
    """
    video = request.files["video"]
    filename = video.filename
    session_id = str(uuid4())
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    project_name = f"{os.path.splitext(filename)[0]}_{timestamp}"

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(save_path)
    three_toggle = config.get_setting("three_point_adjust",True)
    def background_task():
        try:
            tracker = ProgressTracker(session_id)
            tracker.update(0, "Initializing...")

            ffmpeg_bin = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
            ffprobe_bin = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"

            rotation = get_rotation_angle(save_path, ffprobe_bin)
            tracker.update(10, "Fixing video rotation")
            rewrite_video(save_path, save_path, rotation, ffmpeg_bin)
            
            print(f"[DEBUG] Looking for video at: {save_path}")
            print(f"[DEBUG] File exists? {os.path.exists(save_path)}")
            print(f"[DEBUG] All files in upload folder: {os.listdir(app.config['UPLOAD_FOLDER'])}")
            if config.get_setting("auto_ai", True):
                tracker.update(25, "Detecting hoop")
                selected = find_hoop(save_path,three_toggle)
                if not selected:
                    tracker.error_occurred("Auto detection failed.")
                    return

                project_path = os.path.join(BASE_DIR, "projects", project_name)
                clips_path = os.path.join(project_path, "clips")
                plots_path = os.path.join(project_path, "plots")
                logs_path = os.path.join(project_path, "logs.txt")
                os.makedirs(clips_path, exist_ok=True)
                os.makedirs(plots_path, exist_ok=True)

                tracker.update(40, "Running detection")
                timestamps, make_miss = detection_model(selected, save_path, plots_path, logs_path,tracker)
                tracker.update(80, "Saving clips")
                save_clips(clips_path, timestamps, make_miss, save_path, ffmpeg_bin,tracker)

                tracker.complete()
            else:
                tracker.error_occurred("Manual selection required")
        except Exception as e:
            tracker.error_occurred(str(e))

    Thread(target=background_task).start()

    return jsonify({"session_id": session_id, "project_name": project_name})
@app.route("/progress-stream/<session_id>")
def progress_stream(session_id):
    def generate():
        while True:
            progress = processing_progress.get(session_id, {})
            yield f"data: {json.dumps(progress)}\n\n"

            if progress.get("is_complete") or progress.get("error"):
                break
            time.sleep(1)
    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    
    app.run(debug=True)

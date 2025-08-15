import subprocess

def get_rotation_angle(video_path):
    """
    Function description: test the effects of rotation on metadata and openCV interactions 
    """
    cmd = [
        "C:/ffmpeg/ffprobe.exe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream_tags=rotate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        rotation = int(output.decode().strip())
        return rotation  # usually 0, 90, 180, or 270
    except subprocess.CalledProcessError:
        return 0  # ffprobe failed (no rotate tag or other error)
    except ValueError:
        return 0  # output exists but isn't a number

# Example usage:
video_path = "./test_videos/bank shot three.mov"
rotation = get_rotation_angle(video_path)
print(f"Rotation: {rotation}°")

import subprocess

import json

def get_rotation_angle(video_path):
    try:
        cmd = [
            "C:/ffmpeg/ffprobe.exe", "-v", "error",
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
video_path = "./test_videos/bank shot three.mov"
rotation = get_rotation_angle(video_path)
print(f"Rotation: {rotation}°")
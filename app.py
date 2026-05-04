import os
import subprocess
import threading
import time
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# Configuration
BASE_RTSP_URL = "rtsp://admin:admin%40123@117.216.45.115:554/Streaming/Channels/"
HLS_BASE_DIR = os.path.join("static", "live")

# Define 16 channels using Substream 2 (X02 pattern)
CHANNELS = {
    f"channel{i}": {
        "name": f"Camera {i}",
        "url": f"{BASE_RTSP_URL}{i}02",
        "dir": os.path.join(HLS_BASE_DIR, f"channel{i}"),
        "file": os.path.join(HLS_BASE_DIR, f"channel{i}", "stream.m3u8")
    } for i in range(1, 17)
}

# Ensure all HLS directories exist
for ch_data in CHANNELS.values():
    os.makedirs(ch_data["dir"], exist_ok=True)

def start_ffmpeg(channel_id, rtsp_url, m3u8_file):
    """Starts the FFmpeg process for a specific channel."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-c:v", "copy",
        "-c:a", "aac",
        "-hls_time", "2",
        "-hls_list_size", "3",  # Reduced list size for 16 channels to save space/memory
        "-hls_flags", "delete_segments",
        "-f", "hls",
        m3u8_file
    ]
    
    while True:
        print(f"Starting FFmpeg for {channel_id}...")
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Monitor the process
        while process.poll() is None:
            time.sleep(10)
        
        print(f"FFmpeg for {channel_id} died. Restarting in 5 seconds...")
        time.sleep(5)

# Start FFmpeg for each channel in background threads
for ch_id, ch_data in CHANNELS.items():
    thread = threading.Thread(target=start_ffmpeg, args=(ch_id, ch_data["url"], ch_data["file"]), daemon=True)
    thread.start()

@app.route("/")
def index():
    return render_template("index.html", channels=CHANNELS)

@app.route("/status")
def status():
    """Returns the status of all channels."""
    results = {}
    for ch_id, ch_data in CHANNELS.items():
        results[ch_id] = "online" if os.path.exists(ch_data["file"]) else "offline"
    return results

@app.route("/stream/<channel_id>/<path:filename>")
def serve_stream(channel_id, filename):
    if channel_id in CHANNELS:
        return send_from_directory(CHANNELS[channel_id]["dir"], filename)
    return "Not Found", 404

if __name__ == "__main__":
    # Use 0.0.0.0 to be reachable in Docker/Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

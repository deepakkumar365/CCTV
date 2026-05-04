import os
import subprocess
import threading
import time
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# Configuration
RTSP_URL = "rtsp://admin:admin%40123@117.216.45.115:554/Streaming/Channels/101"
HLS_DIR = os.path.join("static", "live")
M3U8_FILE = os.path.join(HLS_DIR, "stream.m3u8")

# Ensure the HLS directory exists
os.makedirs(HLS_DIR, exist_ok=True)

def start_ffmpeg():
    """Starts the FFmpeg process to convert RTSP to HLS."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-c:v", "copy",
        "-c:a", "aac",  # Transcode audio to AAC for better browser support
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_flags", "delete_segments",
        "-f", "hls",
        M3U8_FILE
    ]
    
    while True:
        print("Starting FFmpeg...")
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        # Monitor the process
        while process.poll() is None:
            # You could read stderr/stdout here for debugging
            # line = process.stdout.readline()
            time.sleep(5)
        
        print("FFmpeg process died. Restarting in 5 seconds...")
        time.sleep(5)

# Start FFmpeg in a background thread
ffmpeg_thread = threading.Thread(target=start_ffmpeg, daemon=True)
ffmpeg_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/live")
def live():
    # This can be used to check if the stream is active
    stream_exists = os.path.exists(M3U8_FILE)
    return {"status": "online" if stream_exists else "offline"}

@app.route("/stream/<path:filename>")
def serve_stream(filename):
    return send_from_directory(HLS_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

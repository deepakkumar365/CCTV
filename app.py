import os
import subprocess
import threading
import time
from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

# Configuration for multiple companies
# To add a new company, simply add an entry here
COMPANIES = {
    "sgms": {
        "name": "SGMS Old Age home",
        "rtsp_base": "rtsp://admin:admin%40123@117.216.45.115:554/Streaming/Channels/",
        "num_channels": 16,
        "stream_suffix": "02" # Substream 2
    },
    # "other_company": {
    #     "name": "Other Company CCTV",
    #     "rtsp_base": "rtsp://user:pass@IP:port/Streaming/Channels/",
    #     "num_channels": 4,
    #     "stream_suffix": "02"
    # }
}

HLS_BASE_DIR = os.path.join("static", "live")

def get_channel_config(company_id):
    """Generates channel configuration for a specific company."""
    if company_id not in COMPANIES:
        return None
    
    comp = COMPANIES[company_id]
    channels = {}
    for i in range(1, comp["num_channels"] + 1):
        ch_id = f"channel{i}"
        channels[ch_id] = {
            "name": f"Camera {i}",
            "url": f"{comp['rtsp_base']}{i}{comp['stream_suffix']}",
            "dir": os.path.join(HLS_BASE_DIR, company_id, ch_id),
            "file": os.path.join(HLS_BASE_DIR, company_id, ch_id, "stream.m3u8")
        }
    return channels

def start_ffmpeg(company_id, channel_id, rtsp_url, m3u8_file):
    """Starts the FFmpeg process for a specific channel of a company."""
    os.makedirs(os.path.dirname(m3u8_file), exist_ok=True)
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-c:v", "copy",
        "-c:a", "aac",
        "-hls_time", "2",
        "-hls_list_size", "3",
        "-hls_flags", "delete_segments",
        "-f", "hls",
        m3u8_file
    ]
    
    while True:
        print(f"Starting FFmpeg for {company_id}/{channel_id}...")
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        while process.poll() is None:
            time.sleep(10)
        
        print(f"FFmpeg for {company_id}/{channel_id} died. Restarting in 5 seconds...")
        time.sleep(5)

# Start FFmpeg threads for all configured companies
for comp_id in COMPANIES:
    channels = get_channel_config(comp_id)
    for ch_id, ch_data in channels.items():
        thread = threading.Thread(
            target=start_ffmpeg, 
            args=(comp_id, ch_id, ch_data["url"], ch_data["file"]), 
            daemon=True
        )
        thread.start()

@app.route("/")
def home():
    return "CCTV Monitoring System Active. Use /company/<id> to view streams."

@app.route("/company/<company_id>")
def company_view(company_id):
    if company_id not in COMPANIES:
        abort(404)
    
    channels = get_channel_config(company_id)
    return render_template("index.html", company=COMPANIES[company_id], channels=channels, company_id=company_id)

@app.route("/status/<company_id>")
def status(company_id):
    if company_id not in COMPANIES:
        abort(404)
        
    channels = get_channel_config(company_id)
    results = {}
    for ch_id, ch_data in channels.items():
        results[ch_id] = "online" if os.path.exists(ch_data["file"]) else "offline"
    return results

@app.route("/stream/<company_id>/<channel_id>/<path:filename>")
def serve_stream(company_id, channel_id, filename):
    channels = get_channel_config(company_id)
    if channels and channel_id in channels:
        return send_from_directory(channels[channel_id]["dir"], filename)
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

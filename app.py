from flask import Flask, request, send_file, jsonify
import os, sys, subprocess, socket
import yt_dlp

# ✅ yt-dlp auto-update
def auto_update_ytdlp():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        import yt_dlp.version
        print(f"yt-dlp updated to version: {yt_dlp.version.__version__}")
    except Exception as e:
        print(f"yt-dlp auto-update failed: {e}")

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
last_files = {}

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ==================== VIDEO/AUDIO DOWNLOAD ====================
@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(force=True) or {}
    url = data.get("url")
    type_ = data.get("type", "mp4")        # mp4 বা mp3
    res = str(data.get("res", "1080")).strip()   # ভিডিও resolution
    bitrate = str(data.get("bitrate", "192")).strip()  # অডিও bitrate

    if not url:
        return jsonify({"error": "URL required"}), 400

    if type_ == "mp3":
        format_str = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate,
        }]
        merge_format = None
    else:
        if res.isdigit():
            format_str = f"bestvideo[height<={res}]+bestaudio/best"
        else:
            format_str = "bestvideo+bestaudio/best"
        postprocessors = []
        merge_format = "mp4"

    ydl_opts = {
        "format": format_str,
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "merge_output_format": merge_format,
        "postprocessors": postprocessors,
        "ignoreerrors": True,
        "noplaylist": True,
        "quiet": True,
        "extractor_args": {"youtube": {"player_client": ["default"]}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type_ == "mp3":
                filename = filename.rsplit(".", 1)[0] + ".mp3"
            last_files[type_] = filename

        return send_file(filename, as_attachment=True,
                         download_name=os.path.basename(filename))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RUN SERVER ====================
if __name__ == "__main__":
    auto_update_ytdlp()
    ip = get_ip()
    print(f"Server running at: http://{ip}:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)

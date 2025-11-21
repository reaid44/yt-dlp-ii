from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import os
import sys
import socket
import subprocess
import yt_dlp
import threading

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# yt-dlp অটো আপডেট
def auto_update_ytdlp():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        print("yt-dlp আপডেট হয়েছে!")
    except Exception as e:
        print(f"yt-dlp আপডেট ফেইল: {e}")

# লোকাল IP বের করা
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ভিডিও ইনফো ফেচ করা
@app.route('/fetch_info', methods=['POST'])
def fetch_info():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL দাও"}), 400

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get("title", "Unknown Title"),
                "channel": info.get("uploader", "Unknown Channel"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ডাউনলোড প্রো (মেইন ফিচার)
@app.route('/download_pro')
def download_pro():
    url = request.args.get('url')
    type_ = request.args.get('type')  # mp4 or mp3
    res = request.args.get('res', '1080')
    bitrate = request.args.get('bitrate', '192')
    playlist = request.args.get('playlist') == '1'

    if not url:
        return "URL নাই!", 400

    # ফরম্যাট সিলেক্ট
    if type_ == 'mp3' or res == 'audio':
        format_selector = 'bestaudio/best'
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }]
    else:
        height = res if res.isdigit() else 1080
        format_selector = f'bestvideo[height<={height}]+bestaudio/bestvideo[height<={height}]/best'
        postprocessors = []

    ydl_opts = {
        'format': format_selector,
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': not playlist,
        'postprocessors': postprocessors,
        'quiet': False,
        'no_warnings': False,
    }

    def start_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    # ব্যাকগ্রাউন্ডে ডাউনলোড চালু
    threading.Thread(target=start_download, daemon=True).start()

    return """
    <h2 style="text-align:center; color:#ffd700; font-family:sans-serif; margin-top:50px;">
    ডাউনলোড শুরু হয়েছে!
    </h2>
    <p style="text-align:center; color:#aaa;">
    ফাইল সেভ হচ্ছে <b>downloads</b> ফোল্ডারে।<br><br>
    <a href="/" style="color:#00d0ff; text-decoration:underline;">← হোমে ফিরে যাও</a>
    </p>
    <script>setTimeout(() => window.location.href = '/', 5000);</script>
    """

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    auto_update_ytdlp()
    ip = get_ip()
    print(f"\nServer চালু হয়েছে → http://{ip}:5000")
    try:
        with open("/sdcard/flask_ip.txt", "w") as f:
            f.write(ip)
        print("IP সেভ হয়েছে /sdcard/flask_ip.txt এ")
    except:
        pass

    app.run(host="0.0.0.0", port=5000, debug=False)

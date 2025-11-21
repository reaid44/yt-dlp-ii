from flask import Flask, render_template, request, send_file, jsonify
import os
import sys
import socket
import subprocess
import yt_dlp

# ==================== অটো আপডেট yt-dlp ====================
def auto_update_ytdlp():
    print("yt-dlp চেক করা হচ্ছে... আপডেট হচ্ছে (যদি দরকার হয়)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "--quiet"
        ])
        import yt_dlp as ydl
        print(f"yt-dlp আপডেট হয়েছে → ভার্সন: {ydl.version.__version__}")
    except Exception as e:
        print(f"yt-dlp আপডেটে সমস্যা: {e}")

# ==================== Flask Setup ====================
app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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

# হোম পেজ
@app.route('/')
def index():
    return render_template('index.html')

# ভিডিও ইনফো ফেচ
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
                "thumbnail": info.get("thumbnail") or "",
                "duration": info.get("duration", 0)
            })
    except Exception as e:
        return jsonify({"error": "ভুল লিংক বা সমস্যা"}), 400

# ==================== মূল ডাউনলোড রুট (ভিডিও/অডিও) ====================
@app.route('/real_download')
def real_download():
    url = request.args.get('url')
    type_ = request.args.get('type')        # mp4 or mp3
    res = request.args.get('res', '1080')   # 1080, 720, audio ইত্যাদি
    bitrate = request.args.get('bitrate', '192')
    playlist = request.args.get('playlist') == '1'

    if not url:
        return "URL নাই!", 400

    # ফরম্যাট সিলেক্ট করা
    if type_ == 'mp3' or res == 'audio':
        format_str = 'bestaudio/best'
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }]
        merge_format = None
    else:
        height = res if str(res).isdigit() else 1080
        format_str = f'bestvideo[height<={height}]+bestaudio/bestvideo[height<={height}]/best'
        postprocessors = []
        merge_format = 'mp4'

    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': not playlist,
        'merge_output_format': merge_format,
        'postprocessors': postprocessors,
        'ignoreerrors': True,   # কোনো লিঙ্ক ফেল করলে বাদ যাবে না
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # MP3 হলে ফাইল এক্সটেনশন ঠিক করা
            if type_ == 'mp3' or res == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            # ফাইল পাঠানো
            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )
    except Exception as e:
        return f"<h2>এরর: {str(e)}</h2>", 500

# ==================== সার্ভার চালু ====================
if __name__ == "__main__":
    auto_update_ytdlp()  # প্রতিবার চালালেই আপডেট চেক করবে
    ip = get_ip()
    print(f"\nClassicTube চালু হয়েছে!")
    print(f"লিংক: http://{ip}:5000")
    print(f"ফাইল সেভ হবে: downloads ফোল্ডারে\n")

    try:
        with open("/sdcard/flask_ip.txt", "w") as f:
            f.write(f"http://{ip}:5000")
        print("IP সেভ হয়েছে /sdcard/flask_ip.txt এ")
    except:
        pass

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

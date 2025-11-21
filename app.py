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

# ==================== মূল ডাউনলোড রুট (শুধু picture) ====================
@app.route('/real_download')
def real_download():
    url = request.args.get('url')
    type_ = request.args.get('type')        # এখন শুধু 'picture' ধরব
    playlist = request.args.get('playlist') == '1'

    if not url:
        return "URL নাই!", 400

    if type_ == 'picture':
        ydl_opts = {
            'skip_download': True,   # ভিডিও/অডিও নামবে না
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'noplaylist': not playlist,
            'writethumbnail': True,  # thumbnail ডাউনলোড করবে
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # thumbnail ফাইল লোকেশন বের করা
                thumb_file = None
                if 'thumbnails' in info and info['thumbnails']:
                    base = ydl.prepare_filename(info)
                    thumb_file = base.rsplit('.', 1)[0] + ".jpg"

                if thumb_file and os.path.exists(thumb_file):
                    return send_file(
                        thumb_file,
                        as_attachment=True,
                        download_name=os.path.basename(thumb_file)
                    )
                else:
                    return "<h2>Thumbnail পাওয়া যায়নি</h2>", 404
        except Exception as e:
            return f"<h2>এরর: {str(e)}</h2>", 500
    else:
        return jsonify({"error": "শুধু picture সাপোর্ট করা হচ্ছে"}), 400

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

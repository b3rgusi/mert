from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import re
import threading

app = Flask(__name__)

# ffmpeg.exe'nin bulunduğu yol
ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')

def is_valid_youtube_url(url):
    regex = r'^(https://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
    return re.match(regex, url) is not None

def get_available_formats(url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            available_formats = [
                f"{fmt['ext']} - {fmt.get('height', 'Audio')}" for fmt in formats if fmt.get('height') is not None
            ]
            available_formats.append("mp3 - En Yüksek Kalite")  # Ses seçeneğini ekle
            return available_formats
    except Exception as e:
        return []

def download_video(url, format_choice, folder_path):
    ydl_opts = {
        'outtmpl': f'{folder_path}/%(title)s.%(ext)s',
        'ffmpeg_location': ffmpeg_path
    }
    
    if "mp3" in format_choice:
        ydl_opts['format'] = 'bestaudio'  # En iyi ses kalitesi
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif "mp4" in format_choice:
        ydl_opts['format'] = 'bestvideo[height=1080]+bestaudio/best'  # Sadece 1080p video ve en iyi ses
    elif "webm" in format_choice:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'  # En iyi kalite WEBM

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/')
def home():
    return render_template('index.html')  # Ana sayfa olarak index.html'i render et

@app.route('/formats', methods=['POST'])
def formats():
    url = request.form.get('url')
    if is_valid_youtube_url(url):
        formats = get_available_formats(url)
        return jsonify({'formats': formats})
    else:
        return jsonify({'error': 'Geçersiz URL'})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    urls = data.get('urls', [])
    formats = data.get('formats', [])
    folder_path = data.get('folder')

    for url, format_choice in zip(urls, formats):
        threading.Thread(target=download_video, args=(url, format_choice, folder_path)).start()

    return jsonify({'message': 'İndirme Başladı'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Ana sayfa için uygun host ve port ayarları

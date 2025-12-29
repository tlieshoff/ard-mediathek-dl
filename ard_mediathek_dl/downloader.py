import os
import requests
import subprocess
from ard_mediathek_dl.ffmpeg import probe_duration
from ard_mediathek_dl.logger import log_info, log_success, log_error

def print_progress_bar(pct):
    bar_length = 40
    filled_length = int(bar_length * pct // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\rDownloading |{bar}| {pct:.2f}% completed", end='', flush=True)

def download_stream(m3u8_url, output_path, debug=False):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    log_info(f"Saving to: {output_path}")

    duration = probe_duration(m3u8_url, debug)

    try:
        cmd = [
            "ffmpeg", "-i", m3u8_url,
            "-c", "copy",
            "-progress", "pipe:1",
            "-loglevel", "error",
            "-y", output_path
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while True:
            line = process.stdout.readline()
            if not line:
                break
            if "out_time_ms=" in line and duration:
                ms = int(line.strip().split("=")[1])
                sec = ms / 1_000_000
                pct = (sec / duration) * 100
                print_progress_bar(pct)

        process.wait()
        print()
        if process.returncode == 0:
            log_success(f"Download complete: {output_path}")
        else:
            log_error("ffmpeg exited with an error.")

    except FileNotFoundError:
        log_error("ffmpeg not found. Please install it.")

def download_subtitle(subtitle_url, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    log_info(f"Saving subtitle to: {output_path}")

    try:
        res = requests.get(subtitle_url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        log_error(f"Failed to download subtitle: {e}")
        return

    try:
        with open(output_path, "w") as file:
            file.write(res.text)
    except OSError as e:
        log_error(f"Unable to write subtitle to file: {e}")

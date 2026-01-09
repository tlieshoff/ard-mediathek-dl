import os
import requests
import subprocess
from typing import Callable, Optional

from ard_mediathek_dl.ffmpeg import probe_duration
from ard_mediathek_dl.logger import log_info, log_success, log_error


ProgressCb = Callable[[float], None]          # pct 0..100
LogCb = Callable[[str], None]                 # log line


def print_progress_bar(pct: float) -> None:
    bar_length = 40
    filled_length = int(bar_length * pct // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f"\rDownloading |{bar}| {pct:.2f}% completed", end='', flush=True)


def download_stream(
    m3u8_url: str,
    output_path: str,
    debug: bool = False,
    progress_cb: Optional[ProgressCb] = None,
    log_cb: Optional[LogCb] = None,
    quiet: bool = False,
) -> None:
    """
    Downloads a stream to output_path using ffmpeg.

    Backwards compatible defaults:
    - prints to console like before
    - progress bar like before

    Web mode can pass:
    - progress_cb(pct)
    - log_cb(line)
    - quiet=True to suppress console noise
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not quiet:
        log_info(f"Saving to: {output_path}")
    if log_cb:
        log_cb(f"Saving to: {output_path}")

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

        last_pct = -1.0

        while True:
            line = process.stdout.readline()
            if not line:
                break

            line = line.strip()
            if log_cb and line:

                log_cb(line)

            if "out_time_ms=" in line and duration:
                ms = int(line.split("=", 1)[1])
                sec = ms / 1_000_000
                pct = max(0.0, min(100.0, (sec / duration) * 100.0))


                if pct - last_pct >= 0.25 or pct == 100.0:
                    last_pct = pct
                    if progress_cb:
                        progress_cb(pct)
                    if not quiet:
                        print_progress_bar(pct)

        process.wait()

        if not quiet:
            print()

        if process.returncode == 0:
            if not quiet:
                log_success(f"Download complete: {output_path}")
            if log_cb:
                log_cb(f"Download complete: {output_path}")
            if progress_cb:
                progress_cb(100.0)
        else:
            if not quiet:
                log_error("ffmpeg exited with an error.")
            if log_cb:
                log_cb("ffmpeg exited with an error.")
    except FileNotFoundError:
        if not quiet:
            log_error("ffmpeg not found. Please install it.")
        if log_cb:
            log_cb("ffmpeg not found. Please install it.")


def download_subtitle(
    subtitle_url: str,
    output_path: str,
    log_cb: Optional[LogCb] = None,
    quiet: bool = False,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not quiet:
        log_info(f"Saving subtitle to: {output_path}")
    if log_cb:
        log_cb(f"Saving subtitle to: {output_path}")

    try:
        res = requests.get(subtitle_url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        if not quiet:
            log_error(f"Failed to download subtitle: {e}")
        if log_cb:
            log_cb(f"Failed to download subtitle: {e}")
        return

    try:
        with open(output_path, "w") as file:
            file.write(res.text)
        if log_cb:
            log_cb(f"Subtitle saved: {output_path}")
    except OSError as e:
        if not quiet:
            log_error(f"Unable to write subtitle to file: {e}")
        if log_cb:
            log_cb(f"Unable to write subtitle to file: {e}")

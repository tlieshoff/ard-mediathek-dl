import subprocess
from ard_mediathek_dl.logger import log_warning, log_debug

def probe_duration(m3u8_url, debug=False):
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", m3u8_url
        ]
        duration = float(subprocess.check_output(cmd).decode().strip())
        log_debug(f"Duration (s): {duration}", debug)
        return duration
    except Exception as e:
        log_warning(f"Could not get duration: {e}")
        return None

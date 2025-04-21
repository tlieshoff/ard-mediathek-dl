# ard-mediathek-dl

This is a small Python command-line tool I created to download videos from the ARD Mediathek. It works by extracting `.m3u8` HLS stream URLs from ARD video pages and then lets you choose a stream to download using `ffmpeg`.

It doesn't bypass any DRM or login walls. It's meant only for publicly available content and is intended for educational, research, or archival purposes.


## Installation

You’ll need Python 3.10 or newer, and `ffmpeg` must be installed and available in your system's path.

To set it up:

```bash
git clone https://github.com/tlieshoff/ard-mediathek-dl.git
cd ard-mediathek-dl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Once installed, you can use the tool via the command `ard-dl`.


## How to use it

1. Go to the ARD Mediathek and open a video page (for example, a *Tatort* episode).
2. Copy the full URL from your browser.
3. Then run:

```bash
ard-dl "https://www.ardmediathek.de/video/..." --download
```

If you only want to see the available qualities (like 720p, 1080p, etc.), run:

```bash
ard-dl "https://www.ardmediathek.de/video/..." --meta
```

It will show all available stream variants, and you can then choose which one to download.


## Other available options

In addition to downloading, you can:

- Use `--stream` to play the video directly in your terminal using `ffplay`
- Use `--play` to open the stream in your system’s default video player
- Add `--auto` to automatically download the best available quality
- Use `--quality 720` (or 1080, best, worst) to manually pick a resolution
- Use `--debug` if you want to see detailed logs

To get a full list of options and help:

```bash
ard-dl --help
```


## License

This tool is open source and licensed under the MIT license.  
See the `LICENSE` file for details.


## Disclaimer

This tool is intended solely for educational and archival purposes.  
You can read the full disclaimer here:  
[DISCLAIMER.md](https://github.com/tlieshoff/ard-mediathek-dl/blob/main/DISCLAIMER.md)

This project is not affiliated with, endorsed by, or sponsored by ARD or any of its affiliates.
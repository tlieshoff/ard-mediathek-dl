# ard-mediathek-dl

`ard-mediathek-dl` is a Python-based tool for downloading and managing **publicly available video content from the ARD Mediathek**.

It provides a command-line interface (CLI) for scripted and automated usage, as well as an optional local web interface for browsing, downloading, and watching content in a browser.

The tool works by extracting `.m3u8` HLS stream URLs from ARD Mediathek video pages and downloading the streams using `ffmpeg`.

It does **not** bypass DRM, authentication mechanisms, or paywalls and only operates on content that is accessible without login.


## Background

This project started as a small personal utility to better understand how ARD Mediathek delivers its content and to make it easier to archive publicly available videos for personal and educational use. A more detailed background and the motivation behind this project are described in this blog post: [https://blog.tobias-lieshoff.de/posts/2025-04-19-83992](https://blog.tobias-lieshoff.de/posts/2025-04-19-83992)


## Scope and Intent

This tool is intended for:

* educational and technical exploration
* research and experimentation
* personal archiving of publicly available content

It is **not** intended as a replacement for official ARD services or distribution platforms.


## How It Works

1. The CLI receives an ARD Mediathek video URL.
2. The HTML page is fetched and parsed.
3. Embedded `.m3u8` HLS playlist URLs are extracted.
4. Available stream variants (resolutions) are detected.
5. A stream is selected (manually or automatically).
6. `ffmpeg` downloads and remuxes the stream into an `.mp4` file.
7. Optional subtitle files (`.vtt`) are downloaded separately.

When the web interface is enabled:

* downloads run in the background
* job status and progress are exposed via a local API
* the web UI polls this API to display live progress
* completed downloads appear automatically in the library view


## Project Structure

```
ard_mediathek_dl/
├── core/            Core extraction and download logic
├── cli.py           Command-line interface entry point
├── web/             Web dashboard (FastAPI)
│   ├── app.py
│   ├── services/    Job queue and library handling
│   ├── templates/   HTML templates
│   └── static/      CSS and JavaScript assets
├── logger.py        Console logging utilities
├── utils.py         URL and naming helpers
└── tests/           Unit tests
```

Legacy top-level modules are retained as thin wrappers for backward compatibility but internally delegate to the `core` package.


## Features

### Command-Line Interface (CLI)

* Download videos from ARD Mediathek URLs
* Inspect available stream variants and resolutions
* Select a specific quality or automatically choose the best available stream
* Download subtitles in WebVTT (`.vtt`) format
* Stream video directly in the terminal using `ffplay`
* Open streams in the system’s default media player
* Enable debug logging for troubleshooting
* Run the web interface alongside CLI downloads

### Web Interface

* Local web dashboard with dark-mode layout
* Overview of all downloaded videos
* Search and filter the local library
* In-browser video playback
* Subtitle support during playback
* Download form (URL, quality, subtitles)
* Background download queue
* Live progress reporting via API


## Requirements

### System Requirements

* Python **3.10+**
* `ffmpeg` and `ffprobe` installed and available on your `PATH`

Install ffmpeg:

**macOS (Homebrew)**

```
brew install ffmpeg
```

**Debian / Ubuntu**

```
sudo apt install ffmpeg
```

For other platforms, see:
[https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Python Dependencies

All Python dependencies are defined in `requirements.txt`.


## Installation

```
git clone https://github.com/tlieshoff/ard-mediathek-dl.git
cd ard-mediathek-dl

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```


## CLI Usage

### Download a video

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." --download
```

### Download with subtitles

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." \
  --download --download-subtitles
```

### Show available stream variants

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." --meta
```

### Automatically select best quality

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." \
  --auto --download
```

### Stream directly in the terminal

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." --stream
```

### Open stream in system player

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." --play
```

### Enable debug logging

```
python -m ard_mediathek_dl.cli "https://www.ardmediathek.de/video/..." --debug
```


## Web Interface

### Start the web dashboard

```
python -m ard_mediathek_dl.cli --web
```

The interface is available at:

```
http://127.0.0.1:8080
```

### Start web dashboard and download in one run

```
python -m ard_mediathek_dl.cli \
  "https://www.ardmediathek.de/video/..." \
  --download --download-subtitles --web
```

The web interface starts immediately and remains available after the download finishes.


## Download Structure

Downloaded files are organized automatically:

```
downloads/
  <series>/
    <air-date>/
      <episode>.mp4
      <episode>/
        <subtitle>.vtt
```

Example:

```
downloads/tatort/2026-01-09/nachtschatten.mp4
```


## Development and Testing

Run unit tests:

```
pytest
```

Run syntax checks:

```
python -m compileall ard_mediathek_dl
```


## License

This project is licensed under the **MIT License**.
See the `LICENSE` file for details.


## Disclaimer

This tool is intended solely for educational and archival purposes. It must not be used to download, store, or redistribute copyrighted content without proper authorization from the rights holder. The author assumes no responsibility for misuse of this software. This project is not affiliated with, endorsed by, or sponsored by ARD or any of its affiliates.
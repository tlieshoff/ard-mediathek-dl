"""
Disclaimer

This tool is intended solely for educational and archival purposes.
It must not be used to download, store, or redistribute copyrighted
content without proper authorization from the rights holder.
The author assumes no responsibility for any misuse of this tool.
"""

import argparse
import sys
import os
import subprocess
import threading
import time
from os.path import join

from ard_mediathek_dl.core.extractor import (
    parse_page,
    extract_m3u8_url,
    choose_variant,
    list_variants,
    extract_subtitle_urls,
)
from ard_mediathek_dl.core.utils import (
    extract_clean_slug,
    extract_air_date_from_url,
    extract_subtitle_name,
)
from ard_mediathek_dl.core.downloader import download_stream, download_subtitle
from ard_mediathek_dl.logger import log_info, log_error, log_success


def _start_web_server(host: str, port: int, downloads_dir: str) -> "tuple[threading.Thread, object]":

    try:
        import uvicorn
        from ard_mediathek_dl.web.app import create_app
    except ImportError:
        log_error("Web dependencies not installed. Install: pip install fastapi uvicorn jinja2")
        raise

    app = create_app(downloads_dir=downloads_dir)
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)

    def run():
        server.run()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


    time.sleep(0.25)

    log_info(f"Web dashboard running: http://{host}:{port}")
    return thread, server


def main():
    parser = argparse.ArgumentParser(
        description="ard_mediathek_dl – ARD video downloader CLI",
        epilog="Example: python -m ard_mediathek_dl.cli https://www.ardmediathek.de/video/..."
    )


    parser.add_argument("url", nargs="?", help="ARD video URL to download or stream")
    parser.add_argument("--quality", help="Choose quality (e.g. 720, 1080, best, worst)", default="best")
    parser.add_argument("--meta", action="store_true", help="Show metadata and stream variants")
    parser.add_argument("--download", action="store_true", help="Download selected stream")
    parser.add_argument("--download-subtitles", action="store_true", help="Download subtitles (requires --download)")
    parser.add_argument("--stream", action="store_true", help="Stream in terminal using ffplay")
    parser.add_argument("--play", action="store_true", help="Open in default system player")
    parser.add_argument("--auto", action="store_true", help="Automatically select best quality")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--about", action="store_true", help="Show tool info and exit")


    parser.add_argument("--web", action="store_true", help="Start web dashboard (can be combined with --download)")
    parser.add_argument("--host", default="127.0.0.1", help="Web host (with --web)")
    parser.add_argument("--port", type=int, default=8080, help="Web port (with --web)")
    parser.add_argument("--downloads-dir", default="downloads", help="Downloads directory (with --web)")

    args = parser.parse_args()

    if args.about:
        print("""
ard_mediathek_dl – ARD Mediathek Video Downloader
--------------------------------------------
A CLI tool to grab ARD video streams using ffmpeg.
Automatically organizes files into: downloads/<series>/<airdate>/<episode>.mp4
Built by Tobias Lieshoff • 2025

Disclaimer
----------
This tool is intended solely for educational and archival purposes.
It must not be used to download, store, or redistribute copyrighted
content without proper authorization from the rights holder.
The author assumes no responsibility for any misuse of this tool.
""")
        sys.exit(0)


    if args.download_subtitles and not args.download:
        log_error("--download-subtitles requires --download")
        sys.exit(1)


    server_thread = None
    server_obj = None
    if args.web:
        try:
            server_thread, server_obj = _start_web_server(args.host, args.port, args.downloads_dir)
        except ImportError:
            sys.exit(1)


    if not args.url:
        if args.web:

            log_info("Press Ctrl+C to stop the web dashboard.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                log_info("Stopping web dashboard...")
                if server_obj:
                    server_obj.should_exit = True
                sys.exit(0)

        log_error("Please provide a video URL (or use --web without a URL).")
        parser.print_help()
        sys.exit(1)


    log_info("Starting ard_mediathek_dl...")
    soup = parse_page(args.url)
    if not soup:
        sys.exit(1)

    m3u8_master = extract_m3u8_url(soup, args.debug)
    if not m3u8_master:
        sys.exit(1)

    variants = list_variants(m3u8_master)

    if args.meta:
        log_info("Available stream variants:")
        for idx, (res, uri) in enumerate(variants, 1):
            print(f"{idx}) {res} => {uri}")

        if args.download or args.stream or args.play:
            try:
                choice = int(input("\nEnter stream number to use: "))
                if 1 <= choice <= len(variants):
                    selected_url = variants[choice - 1][1]
                    log_success("Selected stream:")
                    print(selected_url)
                else:
                    log_error("Invalid selection.")
                    sys.exit(1)
            except ValueError:
                log_error("Please enter a valid number.")
                sys.exit(1)
        else:
            sys.exit(0)

    elif args.auto:
        selected_url = choose_variant(m3u8_master, "best", args.debug)
    else:
        selected_url = choose_variant(m3u8_master, args.quality, args.debug)

    if args.stream:
        subprocess.run(["ffplay", selected_url])
        sys.exit(0)

    if args.play:
        if sys.platform == "darwin":
            subprocess.run(["open", selected_url])
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", selected_url])
        elif sys.platform == "win32":
            os.startfile(selected_url)
        else:
            log_error("Unsupported OS for --play.")
        sys.exit(0)

    if args.download:
        series, slug = extract_clean_slug(args.url)
        airdate = extract_air_date_from_url(args.url)
        filename = f"{slug}.mp4"
        outdir = join(args.downloads_dir, series, airdate)
        fullpath = join(outdir, filename)

        download_stream(selected_url, fullpath, args.debug)

        if args.download_subtitles:
            subtitle_urls = extract_subtitle_urls(soup, args.debug)
            sub_dir = join(outdir, slug)
            for sub_url in subtitle_urls:
                download_subtitle(sub_url, join(sub_dir, extract_subtitle_name(sub_url)))


    if args.web:
        log_info("Download finished. Web dashboard is still running.")
        log_info("Press Ctrl+C to stop the web dashboard.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log_info("Stopping web dashboard...")
            if server_obj:
                server_obj.should_exit = True
            sys.exit(0)


if __name__ == "__main__":
    main()

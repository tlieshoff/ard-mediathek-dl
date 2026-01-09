from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from os.path import join

from ard_mediathek_dl.core.extractor import (
    parse_page,
    extract_m3u8_url,
    choose_variant,
    extract_subtitle_urls,
)
from ard_mediathek_dl.core.utils import (
    extract_clean_slug,
    extract_air_date_from_url,
    extract_subtitle_name,
)
from ard_mediathek_dl.core.downloader import download_stream, download_subtitle


@dataclass
class DownloadJob:
    id: str
    url: str
    quality: str
    auto_best: bool
    subtitles: bool
    downloads_dir: str

    status: str = "queued"  # queued|running|done|failed
    progress: float = 0.0   # 0..100
    created_at: float = field(default_factory=lambda: time.time())
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    output_path: Optional[str] = None
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)

    def log(self, msg: str) -> None:
        # keep last N lines
        self.logs.append(msg)
        if len(self.logs) > 400:
            self.logs = self.logs[-400:]


_LOCK = threading.Lock()
_JOBS: Dict[str, DownloadJob] = {}
_QUEUE: List[str] = []

_WORKER_THREAD: Optional[threading.Thread] = None
_WORKER_RUNNING = False


def list_jobs() -> List[DownloadJob]:
    with _LOCK:

        return sorted(_JOBS.values(), key=lambda j: j.created_at, reverse=True)


def get_job(job_id: str) -> Optional[DownloadJob]:
    with _LOCK:
        return _JOBS.get(job_id)


def enqueue_download(
    *,
    url: str,
    quality: str = "best",
    auto_best: bool = False,
    subtitles: bool = True,
    downloads_dir: str = "downloads",
) -> DownloadJob:
    job = DownloadJob(
        id=str(uuid.uuid4()),
        url=url,
        quality=quality,
        auto_best=auto_best,
        subtitles=subtitles,
        downloads_dir=downloads_dir,
    )

    with _LOCK:
        _JOBS[job.id] = job
        _QUEUE.append(job.id)

    _ensure_worker()
    return job


def _ensure_worker() -> None:
    global _WORKER_THREAD, _WORKER_RUNNING
    with _LOCK:
        if _WORKER_THREAD and _WORKER_THREAD.is_alive():
            return
        _WORKER_RUNNING = True
        _WORKER_THREAD = threading.Thread(target=_worker_loop, daemon=True)
        _WORKER_THREAD.start()


def _worker_loop() -> None:
    global _WORKER_RUNNING
    while True:
        job_id = None
        with _LOCK:
            if _QUEUE:
                job_id = _QUEUE.pop(0)
            else:
                # no jobs; stop worker
                _WORKER_RUNNING = False
                return

        job = get_job(job_id) if job_id else None
        if not job:
            continue

        try:
            _run_job(job)
        except Exception as e:
            with _LOCK:
                job.status = "failed"
                job.error = str(e)
                job.finished_at = time.time()
                job.log(f"[ERROR] {e}")


def _run_job(job: DownloadJob) -> None:
    with _LOCK:
        job.status = "running"
        job.started_at = time.time()
        job.progress = 0.0
        job.error = None
        job.logs = []
        job.output_path = None

    job.log("[INFO] Starting download job")
    job.log(f"[INFO] URL: {job.url}")

    soup = parse_page(job.url)
    if not soup:
        raise RuntimeError("Failed to load page")

    m3u8_master = extract_m3u8_url(soup, debug=False)
    if not m3u8_master:
        raise RuntimeError("Could not find m3u8 on page")

    if job.auto_best:
        selected_url = choose_variant(m3u8_master, "best", debug=False)
    else:
        selected_url = choose_variant(m3u8_master, job.quality, debug=False)

    series, slug = extract_clean_slug(job.url)
    airdate = extract_air_date_from_url(job.url)
    filename = f"{slug}.mp4"
    outdir = join(job.downloads_dir, series, airdate)
    fullpath = join(outdir, filename)

    with _LOCK:
        job.output_path = fullpath

    def on_progress(pct: float) -> None:
        with _LOCK:
            job.progress = pct

    def on_log(line: str) -> None:
        job.log(line)

    download_stream(
        selected_url,
        fullpath,
        debug=False,
        progress_cb=on_progress,
        log_cb=on_log,
        quiet=True,
    )

    # subtitles
    if job.subtitles:
        subtitle_urls = extract_subtitle_urls(soup, debug=False)
        sub_dir = join(outdir, slug)
        for sub_url in subtitle_urls:
            download_subtitle(
                sub_url,
                join(sub_dir, extract_subtitle_name(sub_url)),
                log_cb=on_log,
                quiet=True,
            )

    with _LOCK:
        job.status = "done"
        job.progress = 100.0
        job.finished_at = time.time()

    job.log("[SUCCESS] Job finished")

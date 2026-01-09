from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ard_mediathek_dl.web.services.library import (
    scan_downloads,
    search_items,
    to_public_dict,
    find_item,
)
from ard_mediathek_dl.web.services.jobs import (
    enqueue_download,
    list_jobs,
    get_job,
)


def _is_within(base: Path, target: Path) -> bool:
    base = base.resolve()
    target = target.resolve()
    return base == target or base in target.parents


def _job_public(job) -> dict:
    return {
        "id": job.id,
        "url": job.url,
        "quality": job.quality,
        "autoBest": job.auto_best,
        "subtitles": job.subtitles,
        "downloadsDir": job.downloads_dir,
        "status": job.status,
        "progress": job.progress,
        "createdAt": job.created_at,
        "startedAt": job.started_at,
        "finishedAt": job.finished_at,
        "outputPath": job.output_path,
        "error": job.error,
        "logs": job.logs[-200:],
    }


def create_app(downloads_dir: str = "downloads") -> FastAPI:
    app = FastAPI(title="ard_mediathek_dl web")

    web_root = Path(__file__).parent
    templates = Jinja2Templates(directory=str(web_root / "templates"))

    static_dir = web_root / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, q: str = ""):
        items = scan_downloads(downloads_dir)
        filtered = search_items(items, q)
        payload = [to_public_dict(it, downloads_dir) for it in filtered[:500]]

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "downloads_dir": downloads_dir,
                "q": q,
                "items": payload,
                "count_total": len(items),
                "count_filtered": len(filtered),
            },
        )

    @app.get("/api/library", response_class=JSONResponse)
    def api_library(q: str = ""):
        items = scan_downloads(downloads_dir)
        filtered = search_items(items, q)
        payload = [to_public_dict(it, downloads_dir) for it in filtered[:500]]
        return {"query": q, "total": len(items), "count": len(filtered), "items": payload}

    @app.post("/api/download", response_class=JSONResponse)
    def api_download(payload: dict):
        url = (payload.get("url") or "").strip()
        if not url:
            raise HTTPException(status_code=400, detail="Missing url")

        quality = (payload.get("quality") or "best").strip()
        auto_best = bool(payload.get("autoBest", False))
        subtitles = bool(payload.get("subtitles", True))

        job = enqueue_download(
            url=url,
            quality=quality,
            auto_best=auto_best,
            subtitles=subtitles,
            downloads_dir=downloads_dir,
        )
        return {"ok": True, "job": _job_public(job)}

    @app.get("/api/jobs", response_class=JSONResponse)
    def api_jobs() -> dict:
        jobs = list_jobs()
        return {"jobs": [_job_public(j) for j in jobs]}

    @app.get("/api/jobs/{job_id}", response_class=JSONResponse)
    def api_job(job_id: str) -> dict:
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Not found")
        return {"job": _job_public(job)}

    @app.get("/watch/{item_id:path}", response_class=HTMLResponse)
    def watch(request: Request, item_id: str):
        items = scan_downloads(downloads_dir)
        item = find_item(items, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")

        pub = to_public_dict(item, downloads_dir)
        return templates.TemplateResponse("watch.html", {"request": request, "item": pub, "downloads_dir": downloads_dir})

    @app.get("/media/{video_rel:path}")
    def media(video_rel: str):
        base = Path(downloads_dir).resolve()
        target = (base / video_rel).resolve()

        if not target.exists() or not target.is_file() or not _is_within(base, target):
            raise HTTPException(status_code=404, detail="Not found")

        return FileResponse(str(target), media_type="video/mp4")

    @app.get("/subtitle/{sub_rel:path}")
    def subtitle(sub_rel: str):
        base = Path(downloads_dir).resolve()
        target = (base / sub_rel).resolve()

        if not target.exists() or not target.is_file() or not _is_within(base, target):
            raise HTTPException(status_code=404, detail="Not found")

        return FileResponse(str(target), media_type="text/vtt")

    return app


app = create_app()

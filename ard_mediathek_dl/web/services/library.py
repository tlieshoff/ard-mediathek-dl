from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".m4v"}


@dataclass(frozen=True)
class LibraryItem:
    id: str
    title: str
    series: str
    date: str
    video_path: Path
    subtitle_paths: List[Path]
    size_bytes: int
    mtime: float


def _safe_id(video_path: Path, base: Path) -> str:
    return video_path.relative_to(base).as_posix()


def _human_size(num: int) -> str:
    size = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0 or unit == "PB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{int(num)} B"


def _format_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def scan_downloads(downloads_dir: str = "downloads") -> List[LibraryItem]:
    base = Path(downloads_dir).resolve()
    if not base.exists():
        return []

    items: List[LibraryItem] = []

    for video_path in base.rglob("*"):
        if not video_path.is_file():
            continue
        if video_path.suffix.lower() not in VIDEO_EXTS:
            continue

        rel = video_path.relative_to(base)
        parts = rel.parts


        series = parts[0] if len(parts) >= 1 else "unknown"
        date = parts[1] if len(parts) >= 2 else "unknown"
        title = video_path.stem

        subtitle_dir = video_path.parent / video_path.stem
        subs: List[Path] = []
        if subtitle_dir.exists() and subtitle_dir.is_dir():
            subs = sorted([p for p in subtitle_dir.glob("*.vtt") if p.is_file()])

        stat = video_path.stat()
        items.append(
            LibraryItem(
                id=_safe_id(video_path, base),
                title=title,
                series=series,
                date=date,
                video_path=video_path,
                subtitle_paths=subs,
                size_bytes=stat.st_size,
                mtime=stat.st_mtime,
            )
        )


    items.sort(key=lambda x: x.mtime, reverse=True)
    return items


def search_items(items: List[LibraryItem], query: str) -> List[LibraryItem]:
    q = (query or "").strip().lower()
    if not q:
        return items

    def blob(it: LibraryItem) -> str:
        return f"{it.title} {it.series} {it.date} {it.id}".lower()

    return [it for it in items if q in blob(it)]


def find_item(items: List[LibraryItem], item_id: str) -> Optional[LibraryItem]:
    for it in items:
        if it.id == item_id:
            return it
    return None


def to_public_dict(it: LibraryItem, downloads_dir: str) -> dict:
    base = Path(downloads_dir).resolve()
    return {
        "id": it.id,
        "title": it.title,
        "series": it.series,
        "date": it.date,
        "sizeBytes": it.size_bytes,
        "sizeHuman": _human_size(it.size_bytes),
        "mtime": it.mtime,
        "mtimeHuman": _format_mtime(it.mtime),
        "subtitleCount": len(it.subtitle_paths),
        "watchUrl": f"/watch/{it.id}",
        "videoUrl": f"/media/{it.id}",
        "subtitles": [
            {
                "label": sp.name,
                "url": f"/subtitle/{sp.relative_to(base).as_posix()}",
            }
            for sp in it.subtitle_paths
        ],
    }

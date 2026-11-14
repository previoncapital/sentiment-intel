"""Polite fetching into an immutable, content-addressed raw store.

Every downloaded file is kept exactly as received, named by the SHA-256 hash of
its bytes, under ``<root>/<source>/<yyyy>/<mm>/<sha256>.<ext>``. A line is
appended to ``<root>/manifest.jsonl`` for every fetch (URL, time, HTTP headers,
hash, connector version), so any derived fact can be traced to the exact bytes
it came from. A file is never overwritten: if a page changes, its new bytes get
a new hash and a new file.

Locally the root is ``data/raw`` (git-ignored). In production the same layout
lives in object storage.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "data" / "raw"

# Seconds to wait between requests to the same website.
MIN_INTERVAL_PER_HOST = 1.5

_last_request_at: dict[str, float] = {}


def user_agent() -> str:
    """Identify the project honestly. The contact address comes from
    configuration (environment variable), never from code."""
    contact = os.environ.get("SENTIMENT_CONTACT_EMAIL", "contact-not-configured")
    return f"sentiment-intel/0.1 (Toronto housing records research; contact: {contact})"


@dataclass(frozen=True)
class RawFile:
    sha256: str
    source: str
    url: str
    fetched_at: str
    path: Path
    mime_type: str
    connector_version: str

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()


def _ext_for(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix and len(suffix) <= 8:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    return guessed or ".bin"


def _polite_wait(host: str) -> None:
    last = _last_request_at.get(host)
    if last is not None:
        wait = MIN_INTERVAL_PER_HOST - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
    _last_request_at[host] = time.monotonic()


def _manifest_entries(root: Path):
    manifest = root / "manifest.jsonl"
    if not manifest.exists():
        return
    with manifest.open() as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def latest_for_url(url: str, root: Path = DEFAULT_ROOT) -> RawFile | None:
    found = None
    for e in _manifest_entries(root):
        if e["url"] == url:
            found = e
    if found is None or not (root / found["storage_path"]).exists():
        return None
    return RawFile(
        sha256=found["sha256"],
        source=found["source"],
        url=found["url"],
        fetched_at=found["fetched_at"],
        path=root / found["storage_path"],
        mime_type=found["mime_type"],
        connector_version=found["connector_version"],
    )


def fetch(
    url: str,
    source: str,
    connector_version: str,
    *,
    root: Path = DEFAULT_ROOT,
    reuse: bool = True,
    timeout: float = 120.0,
) -> RawFile:
    """Download ``url`` into the raw store and return a handle to it.

    With ``reuse=True`` a URL already in the store is not downloaded again,
    which keeps re-runs fast and avoids needless load on the source site.
    """
    if reuse:
        existing = latest_for_url(url, root)
        if existing is not None:
            return existing

    host = urlparse(url).netloc
    _polite_wait(host)
    resp = httpx.get(
        url,
        headers={"User-Agent": user_agent()},
        follow_redirects=True,
        timeout=timeout,
    )
    resp.raise_for_status()
    body = resp.content
    sha = hashlib.sha256(body).hexdigest()
    now = datetime.now(timezone.utc)
    content_type = resp.headers.get("content-type", "")
    rel = Path(source) / f"{now:%Y}" / f"{now:%m}" / f"{sha}{_ext_for(str(resp.url), content_type)}"
    dest = root / rel
    if not dest.exists():  # immutable: identical bytes are stored once
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(body)
        tmp.rename(dest)

    entry = {
        "sha256": sha,
        "source": source,
        "url": url,
        "final_url": str(resp.url),
        "fetched_at": now.isoformat(timespec="seconds"),
        "http_status": resp.status_code,
        "http_headers": dict(resp.headers),
        "storage_path": str(rel),
        "mime_type": content_type,
        "size_bytes": len(body),
        "connector_version": connector_version,
    }
    root.mkdir(parents=True, exist_ok=True)
    with (root / "manifest.jsonl").open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    return RawFile(sha, source, url, entry["fetched_at"], dest, content_type, connector_version)

"""Turn a Markdown page into a PDF the owner can open on any device.

Needs pandoc and the pre-installed Node Playwright/Chromium.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

CSS = ("body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:11pt;"
       "line-height:1.45;max-width:760px;margin:auto;color:#1f2933}h1{font-size:20pt}"
       "h2{margin-top:1.6em;border-bottom:1px solid #ccd;padding-bottom:.2em}"
       "h3{margin-bottom:.2em;margin-top:1.2em}ul{margin-top:.2em}"
       "table{border-collapse:collapse;font-size:9.5pt}"
       "td,th{border:1px solid #ccd;padding:3px 6px;vertical-align:top}img{width:100%}"
       ".tag{display:inline-block;padding:0 6px;border-radius:4px;background:#eef2f6;font-size:9pt}")


def markdown_to_pdf(markdown: str, pdf_path: Path, title: str) -> Path:
    tmp = Path(tempfile.mkdtemp())
    md, html = tmp / "page.md", tmp / "page.html"
    md.write_text(markdown)
    subprocess.run(["pandoc", str(md), "-s", "-o", str(html), "--metadata", f"pagetitle={title}",
                    "-V", f"header-includes=<style>{CSS}</style>"], check=True)
    js = (f"const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();"
          f"const p=await b.newPage();await p.goto('file://{html}');"
          f"await p.pdf({{path:'{pdf_path}',format:'Letter',"
          f"margin:{{top:'18mm',bottom:'18mm',left:'15mm',right:'15mm'}}}});await b.close();}})();")
    subprocess.run(["node", "-e", js], check=True)
    return pdf_path

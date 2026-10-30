from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import __version__

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html", "j2"]),
)


def render_html(filename: str, result: dict) -> str:
    tmpl = _env.get_template("report.html.j2")
    verdict = result.get("verdict")
    label = {"clean": "Verified clean", "improved": "Improved — issues remain", "stale": "Out of date"}.get(verdict, verdict)
    vclass = {"clean": "clean", "improved": "improved"}.get(verdict, "other")
    return tmpl.render(
        filename=filename,
        generated_at=datetime.now(timezone.utc).isoformat(),
        version=__version__,
        verdict_label=label,
        verdict_class=vclass,
        before=result.get("before") or {},
        after=result.get("after") or {},
        by_type=result.get("by_type") or [],
    )

#!/usr/bin/env python3
"""Generate GitHub-style repo pin SVGs for user or organization repositories."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

# github-readme-stats pin cards reject organization repos
# ("Organization Repository Not found"). These cards are generated from the
# public GitHub API instead, so org projects like bcb-unl/* can be shown.

DEFAULT_REPOS = [
    {
        "repo": "bcb-unl/run_dbcan",
        "description": "CAZyme annotation pipeline (dbCAN v5)",
    },
    {
        "repo": "bcb-unl/dbcan-nf",
        "description": "Nextflow workflow for microbiome CAZymes",
    },
]

LANG_COLORS = {
    "Python": "#3572A5",
    "Nextflow": "#0A8A6A",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "R": "#198CE7",
    "C": "#555555",
    "C++": "#f34b7d",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Dockerfile": "#384d54",
}

USER_AGENT = "Xinpeng021001-profile-cards"


def format_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1_000:
        return f"{value / 1_000:.1f}k".replace(".0k", "k")
    return str(value)


def wrap_text(text: str, width: int = 46, max_lines: int = 2) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if len(trial) <= width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and (
        current not in lines or len(" ".join(words)) > width * max_lines
    ):
        lines[-1] = lines[-1].rstrip(" .") + "…"
    return lines or [""]


def github_get(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {url}: {body}") from exc


def render_pin(data: dict, description: str | None) -> str:
    owner = data["owner"]["login"]
    name = data["name"]
    title = f"{owner}/{name}"
    desc = description or data.get("description") or "No description provided."
    stars = format_count(int(data.get("stargazers_count") or 0))
    forks = format_count(int(data.get("forks_count") or 0))
    language = data.get("language") or "Repo"
    lang_color = LANG_COLORS.get(language, "#8b949e")
    desc_lines = wrap_text(desc)

    desc_svg = "\n".join(
        f'<text x="25" y="{72 + i * 16}" class="desc">{escape(line)}</text>'
        for i, line in enumerate(desc_lines)
    )
    stats_y = 72 + max(len(desc_lines), 1) * 16 + 18
    height = max(120, stats_y + 22)

    return f"""<svg width="400" height="{height}" viewBox="0 0 400 {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">{escape(desc)}</desc>
  <style>
    .title {{ font: 600 15px 'Segoe UI', Ubuntu, Sans-Serif; fill: #2f80ed; }}
    .desc {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #434d58; }}
    .meta {{ font: 600 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: #434d58; }}
    .icon {{ fill: #434d58; }}
  </style>
  <rect x="0.5" y="0.5" width="399" height="{height - 1}" rx="6" fill="#fffefe" stroke="#e4e2e2"/>
  <g transform="translate(25, 22)">
    <svg class="icon" viewBox="0 0 16 16" width="14" height="14" x="0" y="0">
      <path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
    </svg>
  </g>
  <text x="46" y="34" class="title">{escape(title)}</text>
  {desc_svg}
  <g transform="translate(25, {stats_y})">
    <svg class="icon" viewBox="0 0 16 16" width="12" height="12" y="-10">
      <path fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>
    </svg>
    <text x="16" y="0" class="meta">{escape(stars)}</text>
    <svg class="icon" viewBox="0 0 16 16" width="12" height="12" x="58" y="-10">
      <path fill-rule="evenodd" d="M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"/>
    </svg>
    <text x="76" y="0" class="meta">{escape(forks)}</text>
    <circle cx="128" cy="-4" r="6" fill="{lang_color}"/>
    <text x="140" y="0" class="meta">{escape(language)}</text>
  </g>
</svg>
"""


def repo_to_filename(full_name: str) -> str:
    return "pin-" + full_name.replace("/", "-") + ".svg"


def generate_pins(repos: list[dict], outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in repos:
        full_name = item["repo"]
        if "/" not in full_name:
            raise ValueError(f"Expected owner/repo, got {full_name!r}")
        data = github_get(f"https://api.github.com/repos/{full_name}")
        actual = data["full_name"]
        svg = render_pin(data, item.get("description"))
        path = outdir / repo_to_filename(actual)
        path.write_text(svg, encoding="utf-8")
        written.append(path)
        print(f"wrote {path} ({actual} ★{data.get('stargazers_count', 0)})")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="JSON list of {repo, description?} objects",
    )
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="owner/repo (repeatable). Optional ::custom description",
    )
    parser.add_argument("--outdir", type=Path, default=Path("profile"))
    args = parser.parse_args()

    repos: list[dict] = []
    if args.config:
        repos = json.loads(args.config.read_text(encoding="utf-8"))
    for spec in args.repo:
        if "::" in spec:
            name, desc = spec.split("::", 1)
            repos.append({"repo": name, "description": desc})
        else:
            repos.append({"repo": spec})
    if not repos:
        repos = DEFAULT_REPOS

    generate_pins(repos, args.outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

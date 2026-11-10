"""
Builds dark_mode.svg and light_mode.svg: an ASCII portrait on the left and a
neofetch-style info panel on the right, with live GitHub stats.

Run locally:      python scripts/generate.py
With full stats:  GH_TOKEN=<token> python scripts/generate.py

Without a token only public numbers are filled in (repos, stars, followers).
The GitHub Action in .github/workflows/update-stats.yml runs this every day.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

# ----------------------------------------------------------------------------
# Edit these to change what the card says
# ----------------------------------------------------------------------------
USER = os.environ.get("GH_USER", "mekroket")
HANDLE = "oguzkaan@ekin"
BIRTHDAY = date(2003, 1, 1)  # TODO: set your real birthday (used for "Uptime")

# Each entry is (key, value). None = blank "." spacer. ("#", title) = section.
INFO = [
    ("OS", "Windows, Linux, Android"),
    ("Uptime", "{uptime}"),
    ("Host", "Türkiye"),
    ("Kernel", "Backend Developer & MIS Student"),
    ("IDE", "VSCode, Visual Studio, PyCharm"),
    None,
    ("Languages.Programming", "JS, TS, Python, PHP, C#"),
    ("Languages.Computer", "HTML, CSS, SQL, JSON, YAML"),
    ("Languages.Real", "Turkish, English"),
    None,
    ("Focus.Backend", "Node.js, Express, Django, .NET"),
    ("Focus.Data", "MySQL, PostgreSQL, MongoDB"),
    ("Hobbies", "Graphic Design, Open Source"),
    ("#", "Contact"),
    ("Email", "iletisim@oguzkaanekin.site"),
    ("LinkedIn", "oguz-kaan"),
    ("Behance", "oguzkaanekin"),
    ("X", "@Oguzkaanekin"),
    ("#", "GitHub Stats"),
]

WIDTH = 58  # characters per info line
ROOT = Path(__file__).resolve().parent.parent

THEMES = {
    "dark": {
        "bg": "#161b22", "border": "#30363d", "text": "#c9d1d9", "key": "#ffa657",
        "value": "#a5d6ff", "dots": "#616e7f", "add": "#3fb950", "del": "#f85149",
        "art": "#c9d1d9",
    },
    "light": {
        "bg": "#f6f8fa", "border": "#d0d7de", "text": "#24292f", "key": "#953800",
        "value": "#0a3069", "dots": "#a0aab4", "add": "#1a7f37", "del": "#cf222e",
        "art": "#24292f",
    },
}

# ----------------------------------------------------------------------------
# GitHub API
# ----------------------------------------------------------------------------
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _request(url: str, body: dict | None = None) -> tuple[int, object]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-generator"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as err:
        return err.code, None


def graphql(query: str, variables: dict) -> dict:
    status, payload = _request("https://api.github.com/graphql", {"query": query, "variables": variables})
    if status != 200 or not payload or "errors" in payload:
        raise RuntimeError(f"GraphQL failed ({status}): {payload}")
    return payload["data"]


def fetch_owned_repos() -> tuple[list[dict], int, int]:
    """Returns (repos, contributed_count, followers) via GraphQL."""
    q = """
    query($login: String!, $after: String) {
      user(login: $login) {
        followers { totalCount }
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
        repositories(ownerAffiliations: OWNER, first: 100, after: $after) {
          pageInfo { hasNextPage endCursor }
          nodes { name owner { login } stargazerCount isFork }
        }
      }
    }"""
    repos, after = [], None
    while True:
        user = graphql(q, {"login": USER, "after": after})["user"]
        repos += user["repositories"]["nodes"]
        page = user["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            return repos, user["repositoriesContributedTo"]["totalCount"], user["followers"]["totalCount"]
        after = page["endCursor"]


def fetch_commit_total() -> int:
    created = graphql("query($l:String!){user(login:$l){createdAt}}", {"l": USER})["user"]["createdAt"]
    first_year, this_year = int(created[:4]), datetime.now(timezone.utc).year
    parts = []
    for y in range(first_year, this_year + 1):
        parts.append(
            f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
            "{ totalCommitContributions restrictedContributionsCount }"
        )
    data = graphql("query($l:String!){user(login:$l){" + " ".join(parts) + "}}", {"l": USER})["user"]
    return sum(v["totalCommitContributions"] + v["restrictedContributionsCount"] for v in data.values())


def fetch_loc(repos: list[dict]) -> tuple[int, int]:
    """Sums the user's additions/deletions across their own (non-fork) repos."""
    pending = [f'{r["owner"]["login"]}/{r["name"]}' for r in repos if not r["isFork"]]
    added = deleted = 0
    for _ in range(8):  # stats are computed lazily; GitHub answers 202 until ready
        still = []
        for full in pending:
            status, data = _request(f"https://api.github.com/repos/{full}/stats/contributors")
            if status == 202:
                still.append(full)
                continue
            for contributor in data or []:
                if (contributor.get("author") or {}).get("login", "").lower() == USER.lower():
                    for week in contributor["weeks"]:
                        added += week["a"]
                        deleted += week["d"]
        pending = still
        if not pending:
            break
        time.sleep(6)
    return added, deleted


def collect_stats() -> dict:
    stats = {"repos": "-", "contributed": "-", "stars": "-", "commits": "-",
             "followers": "-", "loc": "-", "loc_add": "-", "loc_del": "-"}
    if TOKEN:
        repos, contributed, followers = fetch_owned_repos()
        added, deleted = fetch_loc(repos)
        stats.update(
            repos=len(repos), contributed=contributed, followers=followers,
            stars=sum(r["stargazerCount"] for r in repos), commits=fetch_commit_total(),
            loc=added - deleted, loc_add=added, loc_del=deleted,
        )
    else:  # public-only fallback for local previews
        _, user = _request(f"https://api.github.com/users/{USER}")
        _, repos = _request(f"https://api.github.com/users/{USER}/repos?per_page=100")
        if user:
            stats.update(repos=user["public_repos"], followers=user["followers"])
        if isinstance(repos, list):
            stats["stars"] = sum(r["stargazers_count"] for r in repos)
    return stats


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------
def uptime(born: date, today: date) -> str:
    years = today.year - born.year
    months = today.month - born.month
    days = today.day - born.day
    if days < 0:
        months -= 1
        prev_month_last = (today.replace(day=1) - date.resolution).day
        days += prev_month_last
    if months < 0:
        years -= 1
        months += 12
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"


def fmt(n) -> str:
    return f"{n:,}" if isinstance(n, int) else str(n)


def t(cls: str, text: str) -> str:
    return f'<tspan class="{cls}">{escape(text)}</tspan>'


def kv(key: str, value: str, width: int, prefix: str = ". ") -> tuple[str, int]:
    """'. key: ...... value' padded to `width` chars. Returns (svg, visible_len)."""
    head = f"{prefix}{key}:"
    dots = max(1, width - len(head) - len(value) - 2)
    svg = t("cc", prefix) + t("key", f"{key}:") + t("cc", f" {'.' * dots} ") + t("value", value)
    return svg, len(head) + dots + 2 + len(value)


def info_lines(stats: dict) -> list[str]:
    lines = [t("key", HANDLE) + t("cc", " " + "-" * (WIDTH - len(HANDLE) - 1))]
    age = uptime(BIRTHDAY, date.today())
    for item in INFO:
        if item is None:
            lines.append(t("cc", ". "))
        elif item[0] == "#":
            title = item[1]
            lines.append(t("cc", "- ") + t("text", title) + t("cc", " " + "-" * (WIDTH - len(title) - 3)))
        else:
            svg, length = kv(item[0], item[1].format(uptime=age), WIDTH)
            if length > WIDTH:
                print(f"warning: line for {item[0]!r} is {length} chars (> {WIDTH})")
            lines.append(svg)

    # Stats rows: two columns split by " | "
    left_w = 34
    repos_v = f"{fmt(stats['repos'])} {{Contributed: {fmt(stats['contributed'])}}}"
    a, _ = kv("Repos", repos_v, left_w)
    b, _ = kv("Stars", fmt(stats["stars"]), WIDTH - left_w - 3, prefix="")
    lines.append(a + t("cc", " | ") + b)
    a, _ = kv("Commits", fmt(stats["commits"]), left_w)
    b, _ = kv("Followers", fmt(stats["followers"]), WIDTH - left_w - 3, prefix="")
    lines.append(a + t("cc", " | ") + b)

    loc_detail = f" ( {fmt(stats['loc_add'])}++, {fmt(stats['loc_del'])}-- )"
    head = ". Lines of Code:"
    loc_v = fmt(stats["loc"])
    dots = max(1, WIDTH - len(head) - len(loc_v) - len(loc_detail) - 2)
    lines.append(
        t("cc", ". ") + t("key", "Lines of Code:") + t("cc", f" {'.' * dots} ") + t("value", loc_v)
        + t("text", " ( ") + t("add", f"{fmt(stats['loc_add'])}++") + t("text", ", ")
        + t("del", f"{fmt(stats['loc_del'])}--") + t("text", " )")
    )
    return lines


ART_FONT, ART_LINE = 10, 12.5  # must match COLS/CELL_ASPECT in ascii.py


def build_svg(theme: dict, art: list[str], lines: list[str]) -> str:
    line_h, top = 20, 30
    info_bottom = top + (len(lines) - 1) * line_h
    art_top = 22
    art_bottom = art_top + (len(art) - 1) * ART_LINE
    width, height = 1000, round(max(info_bottom, art_bottom) + 25)
    art_svg = "\n".join(
        f'<tspan x="20" y="{art_top + i * ART_LINE}">{escape(row)}</tspan>' for i, row in enumerate(art)
    )
    info_svg = "\n".join(
        f'<tspan x="425" y="{top + i * line_h}">{row}</tspan>' for i, row in enumerate(lines)
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="Consolas, 'DejaVu Sans Mono', Menlo, 'Courier New', monospace" width="{width}px" height="{height}px" font-size="16px">
<style>
.key {{fill: {theme['key']};}}
.value {{fill: {theme['value']};}}
.cc {{fill: {theme['dots']};}}
.text {{fill: {theme['text']};}}
.add {{fill: {theme['add']};}}
.del {{fill: {theme['del']};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="{width}px" height="{height}px" fill="{theme['bg']}" rx="15"/>
<text x="20" y="{art_top}" fill="{theme['art']}" font-size="{ART_FONT}px" xml:space="preserve">
{art_svg}
</text>
<text x="425" y="{top}" fill="{theme['text']}" xml:space="preserve">
{info_svg}
</text>
</svg>
"""


def main() -> None:
    stats = collect_stats()
    print("stats:", stats)
    lines = info_lines(stats)
    for name, theme in THEMES.items():
        art = (ROOT / f"ascii_{name}.txt").read_text(encoding="utf-8").rstrip("\n").splitlines()
        (ROOT / f"{name}_mode.svg").write_text(build_svg(theme, art, lines), encoding="utf-8")
        print(f"wrote {name}_mode.svg")


if __name__ == "__main__":
    main()

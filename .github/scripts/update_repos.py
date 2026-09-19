#!/usr/bin/env python3
"""
🤖 Auto-update script for the GitHub profile README.
Fetches all public repositories and generates a styled table
between the <!-- REPO-LIST:START --> and <!-- REPO-LIST:END --> markers.
"""

import json
import os
import re
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

GITHUB_USER = "sag1687"
README_PATH = "README.md"
START_MARKER = "<!-- REPO-LIST:START -->"
END_MARKER = "<!-- REPO-LIST:END -->"

# Language → emoji mapping
LANG_EMOJI = {
    "Python": "🐍",
    "JavaScript": "🟨",
    "TypeScript": "🔷",
    "HTML": "🌐",
    "CSS": "🎨",
    "Shell": "🐚",
    "Batchfile": "📦",
    "C": "⚙️",
    "C++": "⚙️",
    "Java": "☕",
    "Dockerfile": "🐳",
    "XSLT": "📄",
    None: "📁",
}

# Language → badge color
LANG_COLOR = {
    "Python": "3776AB",
    "JavaScript": "F7DF1E",
    "TypeScript": "3178C6",
    "HTML": "E34F26",
    "CSS": "1572B6",
    "Shell": "4EAA25",
    "Batchfile": "4D4D4D",
    "C": "A8B9CC",
    "C++": "00599C",
    "Java": "ED8B00",
    "Dockerfile": "2496ED",
    "XSLT": "6E6E6E",
}


def fetch_repos():
    """Fetch all public repositories from GitHub API."""
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{GITHUB_USER}/repos"
            f"?type=public&sort=updated&per_page=100&page={page}"
        )
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            req = Request(url, headers=headers)
            with urlopen(req) as resp:
                data = json.loads(resp.read().decode())
        except URLError as e:
            print(f"⚠️  Error fetching repos (page {page}): {e}")
            break

        if not data:
            break
        repos.extend(data)
        page += 1

    return repos


def format_date(iso_str):
    """Format ISO date string to a human-readable format."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y")


def make_badge(label, value, color):
    """Generate a shields.io badge URL."""
    label_enc = label.replace(" ", "%20").replace("-", "--")
    value_enc = value.replace(" ", "%20").replace("-", "--")
    return (
        f"https://img.shields.io/badge/{label_enc}-{value_enc}-{color}"
        f"?style=flat-square"
    )


def generate_repo_table(repos):
    """Generate the markdown table for repositories."""
    if not repos:
        return (
            "\n<div align=\"center\">\n\n"
            "🚀 *I repository verranno mostrati qui automaticamente "
            "dopo la pubblicazione!*\n\n</div>\n"
        )

    # Filter out the profile repo itself and forks
    repos = [
        r for r in repos
        if not r.get("fork", False)
        and r["name"].lower() != GITHUB_USER.lower()
    ]

    # Sort by last update (most recent first)
    repos.sort(key=lambda r: r.get("updated_at", ""), reverse=True)

    lines = []
    lines.append("")
    lines.append("<div align=\"center\">")
    lines.append("")
    lines.append(f"| | Repository | Linguaggio | ⭐ | Descrizione | Ultimo aggiornamento |")
    lines.append("|:-:|:-----------|:----------:|:--:|:------------|:--------------------:|")

    for i, repo in enumerate(repos, 1):
        name = repo["name"]
        url = repo["html_url"]
        lang = repo.get("language")
        stars = repo.get("stargazers_count", 0)
        desc = repo.get("description", "") or "*Nessuna descrizione*"
        updated = format_date(repo.get("updated_at", ""))
        emoji = LANG_EMOJI.get(lang, "📁")
        lang_display = lang or "—"
        color = LANG_COLOR.get(lang, "555555")

        lang_badge = (
            f"![{lang_display}]"
            f"(https://img.shields.io/badge/-{lang_display}-{color}"
            f"?style=flat-square&logoColor=white)"
        )

        # Truncate description if too long
        if len(desc) > 80:
            desc = desc[:77] + "…"

        star_display = f"⭐ {stars}" if stars > 0 else "—"

        lines.append(
            f"| {emoji} | [**{name}**]({url}) | {lang_badge} | "
            f"{star_display} | {desc} | `{updated}` |"
        )

    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append(
        f"<div align=\"center\">"
        f"<sub>🤖 Aggiornato automaticamente il "
        f"{datetime.now().strftime('%d/%m/%Y alle %H:%M')} UTC "
        f"— Trovati <b>{len(repos)}</b> repository pubblici</sub>"
        f"</div>"
    )
    lines.append("")

    return "\n".join(lines)


def update_readme(repo_table):
    """Replace the content between markers in README.md."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )

    new_content = pattern.sub(
        START_MARKER + repo_table + END_MARKER,
        content,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ README.md aggiornato con successo!")


def main():
    print(f"📡 Fetching repos for {GITHUB_USER}...")
    repos = fetch_repos()
    print(f"📦 Trovati {len(repos)} repository pubblici")

    table = generate_repo_table(repos)
    update_readme(table)


if __name__ == "__main__":
    main()

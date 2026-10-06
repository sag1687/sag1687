#!/usr/bin/env python3
"""
🤖 Auto-update script for the GitHub profile README.
Fetches the issues and pull requests opened in the official QGIS
repositories (github.com/qgis) and generates a table between the
<!-- QGIS-CONTRIB:START --> and <!-- QGIS-CONTRIB:END --> markers.
"""

import json
import os
import re
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

GITHUB_USER = "sag1687"
GITHUB_ORG = "qgis"
README_PATH = "README.md"
START_MARKER = "<!-- QGIS-CONTRIB:START -->"
END_MARKER = "<!-- QGIS-CONTRIB:END -->"


def fetch_items():
    """Fetch all issues and PRs authored by the user in the QGIS organization."""
    items = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/search/issues"
            f"?q=author:{GITHUB_USER}+org:{GITHUB_ORG}"
            f"&sort=created&order=desc&per_page=100&page={page}"
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
            print(f"⚠️  Error fetching QGIS contributions (page {page}): {e}")
            return None

        batch = data.get("items", [])
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    return items


def format_date(iso_str):
    """Format ISO date string to a human-readable format."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y")


def status_label(item):
    """Return a bilingual status label for an issue or pull request."""
    if item.get("pull_request"):
        if item["pull_request"].get("merged_at"):
            return "🟣 accettata / merged"
        return "🟢 aperta / open" if item["state"] == "open" else "⚪ chiusa / closed"
    if item["state"] == "open":
        return "🟢 aperta / open"
    reason = item.get("state_reason")
    if reason == "completed":
        return "✅ completata / completed"
    if reason == "duplicate":
        return "⚪ duplicato / duplicate"
    return "⚪ chiusa / closed"


def generate_table(items):
    """Generate the markdown table for the QGIS contributions."""
    if not items:
        return (
            "\n<div align=\"center\">\n\n"
            "🐞 *Le segnalazioni verranno mostrate qui automaticamente!*\n\n"
            "</div>\n"
        )

    items.sort(key=lambda i: i.get("created_at", ""), reverse=True)

    lines = []
    lines.append("")
    lines.append("<div align=\"center\">")
    lines.append("")
    lines.append("| Data / Date | Tipo / Type | Riferimento | Titolo / Title | Stato / Status |")
    lines.append("|:-----------:|:-----------:|:------------|:---------------|:---------------|")

    for item in items:
        repo = item["repository_url"].split("/repos/", 1)[1]
        kind = "🔀 PR" if item.get("pull_request") else "🐞 Issue"
        ref = f"[{repo}#{item['number']}]({item['html_url']})"
        title = item["title"].replace("|", "\\|")
        if len(title) > 90:
            title = title[:87] + "…"
        lines.append(
            f"| `{format_date(item['created_at'])}` | {kind} | {ref} | "
            f"{title} | {status_label(item)} |"
        )

    issues = sum(1 for i in items if not i.get("pull_request"))
    prs = len(items) - issues

    lines.append("")
    lines.append("</div>")
    lines.append("")
    lines.append(
        f"<div align=\"center\">"
        f"<sub>🤖 Aggiornato automaticamente il "
        f"{datetime.now().strftime('%d/%m/%Y alle %H:%M')} UTC "
        f"— <b>{issues}</b> issue e <b>{prs}</b> pull request "
        f"nei repository ufficiali QGIS</sub>"
        f"</div>"
    )
    lines.append("")

    return "\n".join(lines)


def update_readme(table):
    """Replace the content between markers in README.md."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )

    new_content = pattern.sub(
        lambda _m: START_MARKER + table + END_MARKER,
        content,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ README.md aggiornato con successo!")


def main():
    print(f"📡 Fetching QGIS contributions for {GITHUB_USER}...")
    items = fetch_items()
    if items is None:
        print("⚠️  Sezione non aggiornata (errore API): resta la versione precedente.")
        return
    print(f"🐞 Trovati {len(items)} contributi in github.com/{GITHUB_ORG}")

    table = generate_table(items)
    update_readme(table)


if __name__ == "__main__":
    main()

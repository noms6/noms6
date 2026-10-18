"""Rewrite the "Latest repositories" block in README.md with the newest public repos.

Skips forks, archived repos, the profile repo itself, names listed in EXCLUDE,
and any repo tagged with the topic "hide-from-profile".
"""
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "noms6")
LIMIT = int(os.environ.get("LIMIT", "6"))
EXCLUDE = {n.strip().lower() for n in os.environ.get("EXCLUDE", "").split(",") if n.strip()}
README = os.environ.get("README", "README.md")
START, END = "<!-- RECENT:START -->", "<!-- RECENT:END -->"


def fetch_repos():
    url = f"https://api.github.com/users/{USER}/repos?type=owner&sort=created&direction=desc&per_page=100"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "recent-projects"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as resp:
        return json.load(resp)


def keep(repo):
    return not (
        repo["fork"]
        or repo["archived"]
        or repo["private"]
        or repo["name"].lower() == USER.lower()
        or repo["name"].lower() in EXCLUDE
        or "hide-from-profile" in repo.get("topics", [])
    )


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def build(repos):
    rows = ["| Repository | Description | Language | Created |", "| --- | --- | --- | --- |"]
    for r in repos:
        rows.append(
            f"| [**{r['name']}**]({r['html_url']}) | {cell(r['description'])} "
            f"| {r['language'] or '—'} | {r['created_at'][:10]} |"
        )
    return "\n".join(rows)


def main():
    repos = [r for r in fetch_repos() if keep(r)][:LIMIT]
    with open(README, encoding="utf-8") as f:
        text = f.read()
    if START not in text or END not in text:
        raise SystemExit(f"Markers {START} / {END} not found in {README}")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    new = pattern.sub(lambda _: f"{START}\n{build(repos)}\n{END}", text)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"Updated with {len(repos)} repositories")
    else:
        print("No changes")


if __name__ == "__main__":
    main()

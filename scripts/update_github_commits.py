#!/usr/bin/env python3
"""Gera o card de commits anuais usando a API oficial GitHub GraphQL."""

import datetime as dt
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
OUT = Path("assets/github-commits-ano.svg")


def fetch_contributions(username: str, token: str, now: dt.datetime):
    start = f"{now.year}-01-01T00:00:00Z"
    end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    query = """
        query($user: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $user) {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
              contributionCalendar {
                totalContributions
                weeks { contributionDays { date contributionCount } }
              }
            }
          }
        }
    """
    payload = json.dumps({
        "query": query,
        "variables": {"user": username, "from": start, "to": end},
    }).encode("utf-8")
    request = Request(GRAPHQL_ENDPOINT, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-contributions-workflow",
    }, method="POST")
    try:
        with urlopen(request, timeout=25) as response:
            data = json.load(response)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Não foi possível consultar a API do GitHub: {exc}") from exc
    if data.get("errors"):
        raise RuntimeError("Erro GraphQL: " + str(data["errors"]))
    if not data.get("data", {}).get("user"):
        raise RuntimeError(f"Usuário do GitHub não encontrado: {username}")
    collection = data["data"]["user"]["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    daily = {
        item["date"]: int(item["contributionCount"])
        for week in calendar["weeks"]
        for item in week["contributionDays"]
    }
    return int(collection["totalCommitContributions"]), int(calendar["totalContributions"]), daily


def render_svg(username: str, year: int, commits: int, contributions: int,
               daily: dict, today: dt.date):
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    def node(parent, tag, **attrs):
        return ET.SubElement(parent, f"{{{ns}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})
    def label(parent, value, x, y, size, color, weight=None):
        attrs = {"x": x, "y": y, "font_size": size, "fill": color,
                 "font_family": "Arial, Helvetica, sans-serif"}
        if weight:
            attrs["font_weight"] = weight
        el = node(parent, "text", **attrs)
        el.text = str(value)
    svg = ET.Element(f"{{{ns}}}svg", {"width": "880", "height": "215",
                  "viewBox": "0 0 880 215", "role": "img",
                  "aria-label": f"{commits} commits de {username} no ano {year}"})
    node(svg, "rect", x=1, y=1, width=878, height=213, rx=14,
         fill="#0d1117", stroke="#30363d", stroke_width=2)
    label(svg, f"CONTRIBUIÇÕES • {year}", 25, 38, 15, "#8b949e", "bold")
    label(svg, f"{commits:,}".replace(",", "."), 25, 105, 57, "#e6edf3", "bold")
    label(svg, "commits no ano", 26, 131, 18, "#58a6ff")
    label(svg, f"{contributions:,}".replace(",", ".") + " contribuições totais", 26, 163, 12, "#8b949e")
    label(svg, "Atualizado: " + today.strftime("%d/%m/%Y"), 26, 187, 11, "#6e7681")

    start = dt.date(year, 1, 1)
    sunday = start - dt.timedelta(days=(start.weekday()+1) % 7)
    end = dt.date(year, 12, 31)
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    weeks = (end - sunday).days // 7 + 1
    for w in range(weeks):
        for weekday in range(7):
            day = sunday + dt.timedelta(days=7*w+weekday)
            if not (start <= day <= end):
                continue
            count = daily.get(day.isoformat(), 0) if day <= today else 0
            idx = 0 if count == 0 else 1 if count < 3 else 2 if count < 6 else 3 if count < 10 else 4
            node(svg, "rect", x=246+w*11, y=62+weekday*13, width=9,
                 height=9, rx=2, fill=colors[idx])
    for month in range(1, 13):
        d = dt.date(year, month, 1)
        week = (d - sunday).days // 7
        label(svg, d.strftime("%b"), 246+week*11, 48, 10, "#8b949e")
    for weekday, name in [(1,"Seg"),(3,"Qua"),(5,"Sex")]:
        label(svg, name, 219, 70+weekday*13, 10, "#8b949e")
    label(svg, "Menos", 680, 187, 10, "#8b949e")
    for i, color in enumerate(colors):
        node(svg, "rect", x=717+i*17, y=176, width=11, height=11, rx=2, fill=color)
    label(svg, "Mais", 806, 187, 10, "#8b949e")
    return ET.tostring(svg, encoding="unicode", xml_declaration=False) + "\n"


def main():
    username = os.environ.get("GITHUB_USERNAME", "caiopereira51")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN não configurado (defina via GitHub Actions).")
    now = dt.datetime.now(dt.timezone.utc)
    commits, contributions, daily = fetch_contributions(username, token, now)
    svg = render_svg(username, now.year, commits, contributions, daily, now.date())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"Card atualizado: {commits} commits e {contributions} contribuições em {now.year}.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)

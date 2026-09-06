"""Create and summarize private, manually observed AI visibility baselines."""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

CONFIG = json.loads(Path(__file__).with_name("queries.json").read_text())
STATUSES = {"pending", "observed", "unavailable", "no_ai_overview"}


def own_citation(url):
    parsed = urlsplit(url)
    return parsed.scheme in ("https", "http") and parsed.hostname in ("chojecki.net", "www.chojecki.net") and not parsed.username


def new_baseline(day):
    return {
        "query_version": CONFIG["version"], "date": day.isoformat(),
        "next_review": (day + timedelta(days=CONFIG["interval_days"])).isoformat(),
        "conditions": "Record country, language, account/personalization state, product/model, and search mode.",
        "observations": [
            {"engine": engine, "query_id": query["id"], "prompt": query["prompt"],
             "status": "pending", "mentioned": None, "citation_urls": [],
             "accuracy": "not_assessed", "evidence": ""}
            for engine in CONFIG["engines"] for query in CONFIG["queries"]
        ],
        "referrals": {"status": "pending", "source": "Cloudflare Web Analytics > Visits > Referers",
                      "window_start": (day - timedelta(days=14)).isoformat(), "window_end": day.isoformat(),
                      "timezone": "Asia/Taipei", "reported_visits": None, "ai_referrer_visits": None,
                      "by_referrer": {}, "notes": "Record report counts; absent referrers do not prove no AI visits."},
    }


def summarize(data):
    if data.get("query_version") != CONFIG["version"]:
        raise ValueError("query version differs; compare like-for-like baselines")
    expected = {(engine, q["id"]) for engine in CONFIG["engines"] for q in CONFIG["queries"]}
    seen = set()
    rows = data["observations"]
    prompts = {q["id"]: q["prompt"] for q in CONFIG["queries"]}
    for row in rows:
        key = row["engine"], row["query_id"]
        if key not in expected or key in seen:
            raise ValueError(f"unknown or duplicate observation: {key}")
        seen.add(key)
        if row["prompt"] != prompts[row["query_id"]]:
            raise ValueError(f"prompt changed: {key}; use a new query version")
        if row["status"] not in STATUSES:
            raise ValueError(f"invalid status: {key}")
        if row["status"] == "observed":
            if not isinstance(row["mentioned"], bool) or not row["evidence"].strip():
                raise ValueError(f"observed answer needs mention verdict and evidence: {key}")
        elif row["mentioned"] is not None or row["citation_urls"]:
            raise ValueError(f"unobserved answer cannot carry a score: {key}")
        if row["status"] == "no_ai_overview" and row["engine"] != "google_ai_overview":
            raise ValueError("no_ai_overview applies only to Google AI Overviews")
        if not isinstance(row["citation_urls"], list):
            raise ValueError("citation_urls must be a list")
        for url in row["citation_urls"]:
            if not isinstance(url, str) or urlsplit(url).scheme not in ("http", "https") or not urlsplit(url).hostname:
                raise ValueError(f"invalid citation URL: {url}")
    if seen != expected:
        raise ValueError("baseline must contain every engine/query pair; keep unavailable rows explicit")

    engines = {}
    for engine in CONFIG["engines"]:
        engine_rows = [r for r in rows if r["engine"] == engine]
        observed = [r for r in engine_rows if r["status"] == "observed"]
        cited = sum(any(own_citation(url) for url in r["citation_urls"]) for r in observed)
        engines[engine] = {"observed": len(observed), "planned": len(engine_rows),
                           "mentions": sum(r["mentioned"] for r in observed), "answers_citing_site": cited,
                           "citation_rate": cited / len(observed) if observed else None,
                           "statuses": {status: sum(r["status"] == status for r in engine_rows) for status in sorted(STATUSES)}}
    return {"date": data["date"], "next_review": data["next_review"], "engines": engines,
            "note": "Branded diagnostic queries only. Unobserved answers are excluded, not scored as zero; this is not general search visibility."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "summary"))
    parser.add_argument("file", type=Path)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    if args.command == "init":
        args.file.parent.mkdir(parents=True, exist_ok=True)
        # Preserve existing observations; a new baseline must have a new filename.
        with args.file.open("x") as output:
            json.dump(new_baseline(args.date), output, indent=2)
            output.write("\n")
        print(f"Created {args.file}; next review {args.date + timedelta(days=CONFIG['interval_days'])}")
    else:
        print(json.dumps(summarize(json.loads(args.file.read_text())), indent=2))


if __name__ == "__main__":
    main()

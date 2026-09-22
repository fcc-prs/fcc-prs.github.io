import json
import os
import re
import sys
from datetime import datetime, timezone

from api_client import get_client

# Pricing for claude-opus-4-7 (USD per million tokens)
PRICE_INPUT_PER_MTOK = 5.0
PRICE_OUTPUT_PER_MTOK = 25.0


def load_merged_data(path):
    with open(path) as f:
        return json.load(f)


def load_guidelines(path):
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read().strip()


def format_pr(pr):
    lines = [
        f"### {pr['org']}/{pr['repo']}#{pr['num']}: {pr['title']}",
        f"URL: {pr['url']}",
        f"Author: {pr['author']} | Merged by: {pr['mergedBy']} | Date: {pr['mergedAt']}",
        f"Diff: +{pr['diff']['additions']} -{pr['diff']['deletions']}, {pr['diff']['files']} file(s) changed"
        f" | {pr.get('comments_total', 0)} comment(s), {pr.get('reviews_total', 0)} review(s)",
    ]
    if pr.get('labels'):
        lines.append(f"Labels: {', '.join(pr['labels'])}")
    if pr.get('files'):
        lines.append(f"Changed files: {', '.join(pr['files'])}")
    if pr.get('body'):
        lines.append(f"Description: {pr['body']}")
    for r in pr.get('reviews', []):
        if r.get('body'):
            lines.append(f"Review ({r['state']}) by {r['author']}: {r['body']}")
    for c in pr.get('comments', []):
        lines.append(f"Comment by {c['author']}: {c['body']}")
    return "\n".join(lines)


def build_prompt(prs, period_start, period_end, guidelines):
    pr_blocks = "\n\n".join(format_pr(pr) for pr in prs) if prs else "(no merged PRs this period)"

    return f"""\
Below are pull requests merged in the FCC/Key4hep HEP software ecosystem \
from {period_start} to {period_end}, each with its description and discussion.

{pr_blocks}

---

{guidelines}

Using the descriptions, changed file paths, and comments above to judge importance \
and downstream impact, produce your response in exactly two sections.

**Section 1 — `## Summary`**
A bulleted list following the Include/Style rules above.

**Section 2 — `## Omitted`**
For every PR you chose NOT to include, one line each:
`- [org/repo#num](url) — one-sentence reason for exclusion`

Format the entire response as Markdown."""


def parse_output(text):
    """Split model output into summary paragraphs and omitted list."""
    omitted_match = re.search(r'^##\s+omitted\s*$', text, re.IGNORECASE | re.MULTILINE)
    if omitted_match:
        summary_raw = text[:omitted_match.start()].strip()
        omitted_raw = text[omitted_match.end():].strip()
    else:
        summary_raw = text.strip()
        omitted_raw = ""

    summary_raw = re.sub(r'^##\s+summary\s*\n', '', summary_raw, flags=re.IGNORECASE).strip()
    summary_paragraphs = [p for p in summary_raw.split("\n\n") if p.strip()]

    omitted = []
    for line in omitted_raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("-"):
            continue
        link_match = re.match(r'-\s+\[([^\]]+)\]\(([^)]+)\)\s+[—-]+\s+(.*)', line)
        if link_match:
            omitted.append({
                "pr": link_match.group(1),
                "url": link_match.group(2),
                "reason": link_match.group(3).strip(),
            })
        else:
            omitted.append({"pr": line.lstrip("- "), "url": "", "reason": ""})

    return summary_paragraphs, omitted


def extract_text(response):
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


def compute_cost(usage):
    return round(
        (usage.input_tokens * PRICE_INPUT_PER_MTOK
         + usage.output_tokens * PRICE_OUTPUT_PER_MTOK) / 1_000_000,
        6,
    )


args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a for a in sys.argv[1:] if a.startswith("--")}

data_path = args[0] if len(args) > 0 else "assets/json/merged_data.json"
guidelines_path = args[1] if len(args) > 1 else "summary_guidelines.md"
out_path = args[2] if len(args) > 2 else "assets/json/summary.json"
scheduled = "--scheduled" in flags

data = load_merged_data(data_path)
guidelines = load_guidelines(guidelines_path)
prs = data.get("data", [])

if prs:
    dates = [pr["mergedAt"] for pr in prs if pr.get("mergedAt")]
    period_start = min(dates) if dates else ""
    period_end = max(dates) if dates else ""
else:
    period_end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    period_start = period_end

prompt = build_prompt(prs, period_start, period_end, guidelines)

client = get_client()

system = (
    "You are a technical editor for the FCC (Future Circular Collider) and Key4hep "
    "HEP software ecosystem. Your audience is high-energy physics researchers and "
    "software developers who depend on these packages."
)

print("Calling Claude API...", flush=True)
with client.messages.stream(
    model="claude-opus-4-7",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    system=system,
    messages=[{"role": "user", "content": prompt}],
) as stream:
    response = stream.get_final_message()

raw_text = extract_text(response)
print(f"Received {len(raw_text)} chars of output.", flush=True)

summary_paragraphs, omitted = parse_output(raw_text)
print(f"Summary: {len(summary_paragraphs)} paragraph(s), Omitted: {len(omitted)} PR(s).", flush=True)

usage = response.usage
cost = compute_cost(usage)
print(f"Usage: {usage.input_tokens} in / {usage.output_tokens} out — ${cost:.6f}", flush=True)

output = {
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "period_start": period_start,
    "period_end": period_end,
    "summary": summary_paragraphs,
    "omitted": omitted,
    "usage": {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
    },
    "cost_usd": cost,
}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Wrote {out_path}", flush=True)

if scheduled:
    snapshot = {k: v for k, v in output.items() if k != "omitted"}
    snapshots_dir = os.path.join(os.path.dirname(os.path.abspath(out_path)), "summaries")
    os.makedirs(snapshots_dir, exist_ok=True)

    snapshot_path = os.path.join(snapshots_dir, f"{period_end}.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    print(f"Wrote snapshot {snapshot_path}", flush=True)

    index_path = os.path.join(snapshots_dir, "index.json")
    index = json.load(open(index_path)) if os.path.exists(index_path) else []
    if period_end not in index:
        index = [period_end] + index
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
        print(f"Updated index: {index}", flush=True)

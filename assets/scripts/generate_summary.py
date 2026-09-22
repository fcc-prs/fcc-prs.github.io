import json
import os
import sys
from datetime import datetime, timezone

import anthropic


def load_merged_data(path):
    with open(path) as f:
        return json.load(f)


def build_prompt(prs, period_start, period_end):
    lines = []
    for pr in prs:
        lines.append(
            f"- {pr['org']}/{pr['repo']} #{pr['num']}: {pr['title']} "
            f"(author: {pr['author']}, merged by: {pr['mergedBy']})"
            + (f" [labels: {', '.join(pr['labels'])}]" if pr.get('labels') else "")
        )

    pr_list = "\n".join(lines) if lines else "(no merged PRs this period)"

    return f"""\
Here are the pull requests merged in the FCC/Key4hep HEP software ecosystem \
from {period_start} to {period_end}:

{pr_list}

Produce a concise bulleted list of the most important changes. Prioritise:
1. Breaking changes with potential downstream impact on dependent packages or user code
2. Significant new features
3. Important bug fixes

For each bullet, include the repository and PR number (e.g. key4hep/k4geo#662) and a \
one-sentence explanation of why it matters to physicists or downstream developers.
Omit routine CI bumps, trivial dependency/bot updates, minor documentation edits, \
and other low-impact changes.
Aim for 5-15 bullets total. Format as Markdown."""


def extract_text(response):
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


data_path = sys.argv[1] if len(sys.argv) > 1 else "assets/json/merged_data.json"
data = load_merged_data(data_path)
prs = data.get("data", [])

if prs:
    dates = [pr["mergedAt"] for pr in prs if pr.get("mergedAt")]
    period_start = min(dates) if dates else ""
    period_end = max(dates) if dates else ""
else:
    period_end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    period_start = period_end

prompt = build_prompt(prs, period_start, period_end)

client = anthropic.Anthropic(
    api_key="placeholder",  # Portkey uses x-portkey-api-key, not x-api-key
    base_url=os.environ["ANTHROPIC_BASE_URL"],
    default_headers={"x-portkey-api-key": os.environ["ANTHROPIC_API_KEY"]},
)

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

summary_text = extract_text(response)
print(f"Received {len(summary_text)} chars of summary.", flush=True)

output = {
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "period_start": period_start,
    "period_end": period_end,
    "summary": summary_text,
}

out_path = sys.argv[2] if len(sys.argv) > 2 else "assets/json/summary.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)

print(f"Wrote {out_path}", flush=True)

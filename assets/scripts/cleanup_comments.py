#!/usr/bin/env python3
"""Remove comments.json entries for PRs no longer present in sample.json."""

import json
import re


def make_key(repo, num):
    cleaned = re.sub(r'<[^>]+>', '', repo).strip()
    return f"{cleaned}_{num}"


def main():
    with open('assets/json/sample.json') as f:
        sample = json.load(f)

    valid_keys = {make_key(pr['repo'], pr['num']) for pr in sample['data']}

    with open('assets/json/comments.json') as f:
        comments = json.load(f)

    obsolete = [k for k in comments['data'] if k not in valid_keys]

    if not obsolete:
        print("No obsolete comments found.")
        return

    for k in obsolete:
        del comments['data'][k]

    with open('assets/json/comments.json', 'w') as f:
        json.dump(comments, f, indent=2)
        f.write('\n')

    print(f"Removed {len(obsolete)} obsolete key(s):")
    for k in obsolete:
        print(f"  - {k}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Merge comment patch files into comments.json and delete the patches."""

import glob
import json
import os

COMMENTS_FILE = 'assets/json/comments.json'
PATCHES_GLOB = 'assets/json/patches/*.json'


def main():
    patch_files = sorted(glob.glob(PATCHES_GLOB))

    if not patch_files:
        print("No patch files found.")
        return

    with open(COMMENTS_FILE) as f:
        comments = json.load(f)

    total_comments = 0
    for patch_file in patch_files:
        with open(patch_file) as f:
            try:
                patch = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Skipping {patch_file}: invalid JSON ({e})")
                continue

        for key, new_comments in patch.get('data', {}).items():
            if not isinstance(new_comments, list):
                continue
            if key not in comments['data']:
                comments['data'][key] = []
            comments['data'][key].extend(new_comments)
            total_comments += len(new_comments)

        os.remove(patch_file)
        print(f"Merged and deleted: {patch_file}")

    with open(COMMENTS_FILE, 'w') as f:
        json.dump(comments, f, indent=2)
        f.write('\n')

    print(f"Done: merged {total_comments} comment(s) from {len(patch_files)} patch file(s).")


if __name__ == '__main__':
    main()

import json
import sys
from datetime import datetime, timezone


def date_only(s):
    return s.split('T')[0] if s else ''


def get_login(node):
    return node['login'] if node else ''


def process_prs(prs, org, repo):
    rows = []
    for pr in prs:
        rows.append({
            'org': org,
            'repo': repo,
            'num': pr['number'],
            'title': pr['title'],
            'url': pr['url'],
            'author': get_login(pr.get('author')),
            'mergedAt': date_only(pr.get('mergedAt', '')),
            'mergedBy': get_login(pr.get('mergedBy')),
            'labels': [n['name'] for n in pr.get('labels', {}).get('nodes', [])],
        })
    return rows


input_file = sys.argv[1] if len(sys.argv) > 1 else 'all_merged_prs.json'
with open(input_file) as f:
    data = json.load(f)

pr_list = []

for org_data in data.get('orgs', []):
    org = org_data['login']
    for repo in org_data['repositories']:
        pr_list.extend(process_prs(repo['pullRequests']['nodes'], org, repo['name']))

for repo_data in data.get('repos', []):
    pr_list.extend(process_prs(
        repo_data['pullRequests']['nodes'],
        repo_data['owner'],
        repo_data['name'],
    ))

pr_list.sort(key=lambda r: r['mergedAt'], reverse=True)

output = {
    'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'data': pr_list,
}

with open('merged_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4)
